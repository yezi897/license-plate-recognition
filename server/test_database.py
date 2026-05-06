import pytest
import os
import sqlite3
from database import Database


class TestDatabase:
    @pytest.fixture
    def db(self, tmp_path):
        """创建临时数据库"""
        db_path = str(tmp_path / "test.db")
        return Database(db_path)

    def test_init_creates_table(self, db):
        """测试初始化创建表"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='records'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_add_record(self, db):
        """测试添加记录"""
        db.add_record("京A12345", "蓝色", 98.5, "test.jpg")
        records = db.get_records()
        assert len(records) == 1
        assert records[0]['plate_number'] == "京A12345"
        assert records[0]['color'] == "蓝色"
        assert records[0]['confidence'] == 98.5

    def test_get_records_empty(self, db):
        """测试空记录"""
        records = db.get_records()
        assert records == []

    def test_get_records_multiple(self, db):
        """测试多条记录"""
        db.add_record("京A12345", "蓝色", 98.5, "test1.jpg")
        db.add_record("沪B67890", "绿色", 95.0, "test2.jpg")
        records = db.get_records()
        assert len(records) == 2

    def test_get_records_with_pagination(self, db):
        """测试分页"""
        for i in range(15):
            db.add_record(f"京A{i:05d}", "蓝色", 95.0, f"test{i}.jpg")

        page1 = db.get_records(page=1, per_page=10)
        page2 = db.get_records(page=2, per_page=10)
        assert len(page1) == 10
        assert len(page2) == 5

    def test_get_records_order_desc(self, db):
        """测试按时间倒序"""
        db.add_record("京A11111", "蓝色", 95.0, "test1.jpg")
        db.add_record("沪B22222", "绿色", 90.0, "test2.jpg")
        records = db.get_records()
        assert records[0]['plate_number'] == "沪B22222"

    def test_get_total_count(self, db):
        """测试总数统计"""
        db.add_record("京A11111", "蓝色", 95.0, "test1.jpg")
        db.add_record("沪B22222", "绿色", 90.0, "test2.jpg")
        assert db.get_total_count() == 2
