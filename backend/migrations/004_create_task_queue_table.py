"""
创建任务队列表
"""

from sqlalchemy import text


def upgrade(connection):
    """创建task_queue表"""
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS task_queue (
            id VARCHAR(50) PRIMARY KEY,
            task_type ENUM('document_write', 'evaluation', 'test_set_import') NOT NULL,
            status ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending',
            payload JSON NOT NULL,
            progress FLOAT NOT NULL DEFAULT 0.0,
            result JSON NULL,
            error_message TEXT NULL,
            retry_count INT NOT NULL DEFAULT 0,
            max_retries INT NOT NULL DEFAULT 3,
            started_at DATETIME NULL,
            completed_at DATETIME NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_task_queue_status (status),
            INDEX idx_task_queue_type (task_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """))


def downgrade(connection):
    """删除task_queue表"""
    connection.execute(text("DROP TABLE IF EXISTS task_queue;"))

