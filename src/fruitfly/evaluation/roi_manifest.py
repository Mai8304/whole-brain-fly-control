from __future__ import annotations

from typing import Any

REQUIRED_ROI_MANIFEST_KEYS = {
    "roi_id",
    "short_label",
    "display_name",
    "display_name_zh",
    "group",
    "description_zh",
    "default_color",
    "priority",
}


def build_v1_roi_manifest() -> list[dict[str, Any]]:
    return [
        {
            "roi_id": "AL",
            "short_label": "AL",
            "display_name": "Antennal Lobe",
            "display_name_zh": "触角叶",
            "group": "input-associated",
            "description_zh": "V1 中作为气味输入相关脑区的代表。",
            "default_color": "#4ea8de",
            "priority": 1,
        },
        {
            "roi_id": "LH",
            "short_label": "LH",
            "display_name": "Lateral Horn",
            "display_name_zh": "外侧角",
            "group": "input-associated",
            "description_zh": "V1 中作为输入向中间处理过渡的代表脑区。",
            "default_color": "#56cfe1",
            "priority": 2,
        },
        {
            "roi_id": "PB",
            "short_label": "PB",
            "display_name": "Protocerebral Bridge",
            "display_name_zh": "前大脑桥",
            "group": "core-processing",
            "description_zh": "V1 中作为中央复合体核心处理中枢的一部分展示。",
            "default_color": "#f4a261",
            "priority": 3,
        },
        {
            "roi_id": "FB",
            "short_label": "FB",
            "display_name": "Fan-shaped Body",
            "display_name_zh": "扇形体",
            "group": "core-processing",
            "description_zh": "V1 中作为中央复合体处理层展示。",
            "default_color": "#f6bd60",
            "priority": 4,
        },
        {
            "roi_id": "EB",
            "short_label": "EB",
            "display_name": "Ellipsoid Body",
            "display_name_zh": "椭圆体",
            "group": "core-processing",
            "description_zh": "V1 中作为核心导航/整合相关脑区的代表。",
            "default_color": "#f7d08a",
            "priority": 5,
        },
        {
            "roi_id": "NO",
            "short_label": "NO",
            "display_name": "Noduli",
            "display_name_zh": "节球",
            "group": "core-processing",
            "description_zh": "V1 中作为中央复合体附属处理脑区展示。",
            "default_color": "#e9c46a",
            "priority": 6,
        },
        {
            "roi_id": "LAL",
            "short_label": "LAL",
            "display_name": "Lateral Accessory Lobe",
            "display_name_zh": "外侧附属叶",
            "group": "output-associated",
            "description_zh": "V1 中作为接近运动输出的代表脑区。",
            "default_color": "#e76f51",
            "priority": 7,
        },
        {
            "roi_id": "GNG",
            "short_label": "GNG",
            "display_name": "Gnathal Ganglion",
            "display_name_zh": "颚神经节",
            "group": "output-associated",
            "description_zh": "V1 中作为更靠近身体运动控制的输出相关脑区。",
            "default_color": "#d1495b",
            "priority": 8,
        },
    ]
