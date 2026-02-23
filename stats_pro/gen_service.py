# -*- coding: utf-8 -*-
"""文件生成服务"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .config import PluginConfig
from .constants import PLUGIN_ID, GenMode
from .models import GenRecord
from .stats_service import StatsService
from .utils import get_timestamp

if TYPE_CHECKING:
    pass

logger = logging.getLogger(PLUGIN_ID)


class GenService:
    """文件生成服务"""

    def __init__(self, config: PluginConfig, stats_service: StatsService):
        self.config = config
        self.stats_service = stats_service

    def generate_sum(
        self,
        note: str = "",
        players: list[str] | None = None,
    ) -> GenRecord:
        """生成汇总文件"""
        timestamp = get_timestamp()
        file_name = f"{timestamp}#{note}.json" if note else f"{timestamp}.json"
        file_path = self.config.paths.gen_folder("sum") / file_name

        summed_stats = self.stats_service.sum_all_stats(players)

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(summed_stats, f, indent=4, ensure_ascii=False)

        record = GenRecord(
            time=timestamp,
            name=file_name.replace(".json", ""),
            note=note or None,
            path=str(file_path).replace("\\", "/"),
            abs_path=str(file_path.resolve()).replace("\\", "/"),
        )

        self.config.add_gen_record("sum", record)
        self.config.save()

        return record

    def generate_record(self, note: str = "") -> GenRecord:
        """记录当前统计数据（复制stats目录）"""
        timestamp = get_timestamp()
        folder_name = f"{timestamp}#{note}" if note else timestamp
        record_path = self.config.paths.gen_folder("record") / folder_name

        stats_path = self.config.paths.stats_path

        if record_path.exists():
            shutil.rmtree(record_path)

        shutil.copytree(stats_path, record_path)

        record = GenRecord(
            time=timestamp,
            name=folder_name,
            note=note or None,
            path=str(record_path).replace("\\", "/"),
            abs_path=str(record_path.resolve()).replace("\\", "/"),
        )

        self.config.add_gen_record("record", record)
        self.config.save()

        return record

    def generate_minus(
        self,
        mode: str,
        first_time: str,
        second_time: str,
    ) -> GenRecord | None:
        """生成差值文件"""
        if mode not in ("sum", "record"):
            logger.error(f"Invalid minus mode: {mode}")
            return None

        records = self.config.gen_records.get(mode, {})
        first_record = records.get(first_time)
        second_record = records.get(second_time)

        if not first_record or not second_record:
            logger.error("Cannot find specified records")
            return None

        timestamp = get_timestamp()

        if mode == "sum":
            return self._minus_sum_files(
                first_record, second_record, timestamp
            )
        else:
            return self._minus_record_folders(
                first_record, second_record, timestamp
            )

    def _minus_sum_files(
        self,
        first: GenRecord,
        second: GenRecord,
        timestamp: str,
    ) -> GenRecord:
        """计算两个sum文件的差值"""
        with open(first.abs_path, "r", encoding="utf-8") as f:
            first_data = json.load(f)
        with open(second.abs_path, "r", encoding="utf-8") as f:
            second_data = json.load(f)

        diff = self.stats_service.diff_stats(first_data, second_data)

        file_name = f"{timestamp}.json"
        file_path = self.config.paths.gen_folder("minus") / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(diff, f, indent=4, ensure_ascii=False)

        record = GenRecord(
            time=timestamp,
            name=timestamp,
            note=f"{first.time} - {second.time}",
            path=str(file_path).replace("\\", "/"),
            abs_path=str(file_path.resolve()).replace("\\", "/"),
        )

        self.config.add_gen_record("minus", record)
        self.config.save()

        return record

    def _minus_record_folders(
        self,
        first: GenRecord,
        second: GenRecord,
        timestamp: str,
    ) -> GenRecord:
        """计算两个record文件夹的差值"""
        first_path = Path(first.abs_path)
        second_path = Path(second.abs_path)
        output_path = self.config.paths.gen_folder("minus") / timestamp

        output_path.mkdir(parents=True, exist_ok=True)

        all_files = set()
        for p in [first_path, second_path]:
            if p.exists():
                all_files.update(f.name for f in p.glob("*.json"))

        for file_name in all_files:
            first_file = first_path / file_name
            second_file = second_path / file_name

            first_data: dict[str, Any] = {}
            second_data: dict[str, Any] = {}

            if first_file.exists():
                with open(first_file, "r", encoding="utf-8") as f:
                    first_data = json.load(f)
            if second_file.exists():
                with open(second_file, "r", encoding="utf-8") as f:
                    second_data = json.load(f)

            if first_data or second_data:
                diff = self.stats_service.diff_stats(first_data, second_data)
                if diff:
                    output_file = output_path / file_name
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump({"stats": diff}, f, indent=4, ensure_ascii=False)

        record = GenRecord(
            time=timestamp,
            name=timestamp,
            note=f"{first.time} - {second.time}",
            path=str(output_path).replace("\\", "/"),
            abs_path=str(output_path.resolve()).replace("\\", "/"),
        )

        self.config.add_gen_record("minus", record)
        self.config.save()

        return record

    def delete_record(
        self, mode: str, time: str | None = None
    ) -> list[GenRecord]:
        """删除生成记录"""
        deleted = []

        if mode == "all":
            for m in ("sum", "record", "minus"):
                deleted.extend(self.delete_record(m, time))
            return deleted

        records = self.config.gen_records.get(mode, {})
        times_to_delete = [time] if time and time != "all" else list(records.keys())

        for t in times_to_delete:
            record = self.config.remove_gen_record(mode, t)
            if record:
                path = Path(record.abs_path)
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    elif path.exists():
                        path.unlink()
                    deleted.append(record)
                except OSError as e:
                    logger.error(f"Failed to delete {path}: {e}")

        self.config.save()
        return deleted

    def list_records(self, mode: str) -> dict[str, GenRecord]:
        """列出生成记录"""
        if mode == "all":
            result = {}
            for m in ("sum", "record", "minus"):
                result.update(self.config.gen_records.get(m, {}))
            return result
        return dict(self.config.gen_records.get(mode, {}))
