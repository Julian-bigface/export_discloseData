import json
import os


class JsonStore:
    """通用 JSON 存储工具类"""

    def __init__(self, filename):
        config_dir = "config"
        os.makedirs(config_dir, exist_ok=True)
        self.filepath = os.path.join(config_dir, filename)
        self.load()

    def load(self):
        self.data = {}
        """加载 JSON 文件"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                    return self.data
            except Exception:
                return self.data
        return self.data

    def save(self):
        """保存 JSON 文件"""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[JsonStore] 保存失败: {e}")

    def get_all(self):
        return self.data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def delete(self, key):
        if key in self.data:
            del self.data[key]
            self.save()
