CREATE DATABASE IF NOT EXISTS meetings_db;
USE meetings_db;

-- (선택) 애플리케이션 전용 계정
-- 'change-me'를 원하는 비밀번호로 바꾼 뒤 주석을 풀어 실행하고, .env의 DB_CONN에 같은 계정 정보를 넣는다
-- CREATE USER IF NOT EXISTS 'meetings_app'@'%' IDENTIFIED BY 'change-me';
-- GRANT ALL PRIVILEGES ON meetings_db.* TO 'meetings_app'@'%';
-- FLUSH PRIVILEGES;

-- meetings가 user를 참조하므로 meetings를 먼저 삭제
DROP TABLE IF EXISTS meetings;
DROP TABLE IF EXISTS user;

CREATE TABLE user (
    -- 사용자 고유 ID (Primary Key)
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- 사용자 이름
    name VARCHAR(255) DEFAULT NULL,

    -- 사용자 이메일 (로그인 시 사용)
    email VARCHAR(255) DEFAULT NULL,

    -- 해시 처리된 비밀번호
    hashed_password VARCHAR(255) DEFAULT NULL
);

CREATE TABLE meetings (
    -- 회의록 고유 ID (Primary Key)
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- 작성자 ID (user 테이블의 id와 연결)
    user_id BIGINT DEFAULT NULL,

    title TEXT DEFAULT NULL,

    created_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 회의록 원본 텍스트
    original_meeting TEXT DEFAULT NULL,

    -- LLM이 요약한 회의록 텍스트
    summary_meeting TEXT DEFAULT NULL,

    -- 추출된 핵심 키워드 목록 (JSON 배열)
    keywords JSON DEFAULT NULL,

    -- 추천 뉴스 데이터 (JSON 배열)
    -- URL, 원문, 요약문이 매핑된 객체들의 리스트
    news_items JSON DEFAULT NULL,

    -- 외래 키(Foreign Key) 설정
    -- user_id가 user 테이블의 id를 참조하도록 설정
    -- ON DELETE SET NULL: 사용자가 삭제되어도 회의록 기록은 남도록 설정
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
);
