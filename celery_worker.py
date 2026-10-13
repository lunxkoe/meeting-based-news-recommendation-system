# celery_worker.py
import os
import asyncio
import json
import pymysql
from celery import Celery
from kombu import Queue
from celery.result import allow_join_result
from dotenv import load_dotenv

# [Adapter Import] 리팩토링된 인프라스트럭처 어댑터들
from infrastructure.llm.gemini_adapter import GeminiLLMAdapter
from infrastructure.search.google_search_adapter import GoogleSearchAdapter
from infrastructure.crawler.newspaper_adapter import NewspaperCrawlerAdapter
from infrastructure.ai.sbert_adapter import SbertAdapter

load_dotenv()

# --- 환경 변수 설정 ---
DB_CONN = os.getenv("DB_CONN")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if not DB_CONN:
    raise ValueError("DB_CONN 환경 변수가 설정되지 않았습니다.")

# --- Celery 앱 초기화 ---
celery_app = Celery(
    'tasks',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# --- Celery 설정 (큐 분리 및 라우팅) ---
celery_app.conf.update(
    timezone='Asia/Seoul',
    enable_utc=True,
    
    # 큐 정의: 일반 작업용(cpu_io)과 무거운 연산용(gpu) 분리
    task_queues=(
        Queue('cpu_io', default=True), 
        Queue('gpu'),                  
    ),
    
    # 기본 큐 설정
    task_default_queue='cpu_io',
    
    # 라우팅 설정: S-BERT 태스크는 무조건 'gpu' 큐로 보냄
    task_routes={
        'celery_worker.run_sbert_task': {'queue': 'gpu'}
    }
)

# --- 동기 DB 연결 헬퍼 함수 ---
def get_sync_db_conn():
    from urllib.parse import urlparse
    
    # SQLAlchemy용 URL 접두어 처리
    conn_str = DB_CONN
    if conn_str.startswith("mysql+aiomysql://"):
        conn_str = "mysql://" + conn_str[len("mysql+aiomysql://"):]
        
    try:
        parsed = urlparse(conn_str)
        return pymysql.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"DB 연결 설정 오류: {e}")
        return None

# --- Adapter 인스턴스 초기화 (워커 프로세스 시작 시 생성) ---
gemini_adapter = GeminiLLMAdapter(api_key=os.getenv("GEMINI_API_KEY"))

search_adapter = GoogleSearchAdapter(
    json_api_key=os.getenv("CUSTOM_SEARCH_JSON_API_KEY"),
    engine_id=os.getenv("CUSTOM_SEARCH_ENGINE_API_KEY")
)

crawler_adapter = NewspaperCrawlerAdapter()

# S-BERT 어댑터 (내부적으로 모델 로딩 Singleton 처리됨)
sbert_adapter = SbertAdapter()


# =============================================================================
# [Task 1] GPU 작업: S-BERT 유사도 분석
# 이 작업은 'gpu' 큐를 구독하는 워커에서만 실행됩니다.
# =============================================================================
@celery_app.task(name='celery_worker.run_sbert_task')
def run_sbert_task(summary_meeting: str, news_items_list: list):
    print("  [GPU Task] S-BERT 분석 시작...")
    try:
        # SbertAdapter를 사용하여 유사도 계산 후 상위 뉴스 선별
        result = sbert_adapter.calculate_similarity(summary_meeting, news_items_list)
        print("  [GPU Task] 분석 완료.")
        return result
    except Exception as e:
        print(f"  [GPU Task Error] S-BERT 처리 중 오류: {e}")
        # 오류 발생 시, 단순히 크롤링된 순서대로 상위 5개 반환 (Fallback)
        return news_items_list[:5]


# =============================================================================
# [Task 2] 메인 작업: 뉴스 검색 -> 크롤링 -> (S-BERT 위임) -> 요약 -> 저장
# 이 작업은 'cpu_io' 큐(기본)를 구독하는 워커에서 실행됩니다.
# =============================================================================
@celery_app.task(name='process_news_task', bind=True)
def process_news_task(
    self, 
    meeting_id: int, 
    user_id: int, 
    summary_meeting: str, 
    keyword_meeting_list: list
):
    print(f"[Main Task] 뉴스 분석 프로세스 시작 (meeting_id={meeting_id})")

    try:
        # 1. 뉴스 URL 검색 (IO 작업)
        print(f"  [Step 1] Google 검색 시작 (키워드: {keyword_meeting_list})")
        news_urls = asyncio.run(search_adapter.search_urls(keyword_meeting_list, count=50))
        
        if not news_urls:
            print("  [Step 1] 검색된 뉴스 URL이 없습니다.")
            return "No news urls found."

        # 2. 뉴스 본문 크롤링 (IO 작업)
        print(f"  [Step 2] 크롤링 시작 ({len(news_urls)}개 URL)")
        news_items = asyncio.run(crawler_adapter.crawl_urls(news_urls))
        
        if not news_items:
            print("  [Step 2] 크롤링된 뉴스 내용이 없습니다.")
            return "No crawled content."

        # 3. S-BERT 분석 위임 (GPU 작업 호출 및 대기)
        print("  [Step 3] S-BERT 분석 요청 (GPU 워커로 위임)...")
        try:
            # allow_join_result()를 사용하여 하위 태스크가 끝날 때까지 대기
            with allow_join_result():
                selected_news = run_sbert_task.delay(summary_meeting, news_items).get(timeout=300)
            print(f"  [Step 3] S-BERT 분석 완료 (선별된 뉴스 {len(selected_news)}개)")
        except Exception as e:
            print(f"  [Step 3] S-BERT 태스크 호출 실패: {e}")
            # 실패 시 Fallback
            selected_news = news_items[:5]

        # 4. 뉴스 요약 (LLM API 호출 - IO 작업)
        print(f"  [Step 4] 뉴스 요약 시작 (Gemini API)")
        
        async def summarize_all(items):
            for item in items:
                if item.get('original'):
                    item['summary'] = await gemini_adapter.generate_news_summary(item['original'])
            return items
            
        final_news = asyncio.run(summarize_all(selected_news))
        print("  [Step 4] 뉴스 요약 완료")

        # 5. DB 업데이트 (동기 DB 연결 사용)
        print("  [Step 5] DB 저장 시작")
        conn = get_sync_db_conn()
        if conn:
            try:
                with conn.cursor() as cursor:
                    sql = "UPDATE meetings SET news_items = %s WHERE id = %s"
                    cursor.execute(sql, (json.dumps(final_news, ensure_ascii=False), meeting_id))
                conn.commit()
                print("  [Step 5] DB 저장 성공")
            except Exception as e:
                print(f"  [Step 5 Error] DB 업데이트 실패: {e}")
                conn.rollback()
            finally:
                conn.close()
        else:
            print("  [Step 5 Error] DB 연결 실패")

        return f"Task Completed: meeting_id={meeting_id}, news_count={len(final_news)}"

    except Exception as e:
        print(f"[Main Task Error] 작업 실패: {e}")
        # 필요 시 재시도 로직 활성화
        # raise self.retry(exc=e, countdown=60)