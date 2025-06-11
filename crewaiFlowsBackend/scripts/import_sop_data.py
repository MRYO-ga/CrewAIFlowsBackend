# SOP数据导入脚本
import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.database import get_db
from services.sop_service import SOPService

def import_sop_data():
    """导入SOP数据"""
    print("正在导入SOP数据...")
    
    # SOP JSON数据
    sop_json_data = {
        "id": "7bff548c-3480-40a3-875a-b4ca2dc1e8c8",
        "title": "小红书账号周期运营 SOP（3个月版）",
        "type": "operation_sop",
        "cycles": [
            {
                "id": "cold-start",
                "title": "冷启动期",
                "subtitle": "第1-4周：账号定位与测试",
                "duration": "4周",
                "status": "process",
                "icon": "RocketOutlined",
                "color": "#1890ff",
                "progress": 75,
                "goal": "完成账号基建，测试内容模型，锁定核心人群",
                "weeks": [
                    {
                        "id": "week-1",
                        "title": "第1周：账号装修与内容储备（基建搭建）",
                        "status": "finish",
                        "tasks": [
                            {
                                "id": "daily-checklist-1",
                                "category": "每日执行清单（第1-7天）",
                                "completed": False,
                                "items": [
                                    {
                                        "id": "account-setup",
                                        "time": "第1-2天",
                                        "action": "账号装修",
                                        "content": "头图：3宫格设计（选购3步曲图标 + 场景图轮播 + IP形象）简介：突出「年轻人睡眠解决方案」+ 导流钩子",
                                        "example": "头图文案：点击解锁→3步选对床垫简介：帮1000+租房党选到梦中情垫",
                                        "publishTime": "随时完成",
                                        "reason": "建立专业形象，引导用户互动",
                                        "completed": True
                                    },
                                    {
                                        "id": "content-production",
                                        "time": "第3-5天",
                                        "action": "内容生产",
                                        "content": "储备10篇泛用户内容：3篇萌宠图文、2条租房视频、2条剧情口播、2篇数据图文、1套场景海报",
                                        "example": "《猫主子认证！这款床垫让我告别每天除毛》《20㎡出租屋改造：800元床垫逆袭指南》",
                                        "publishTime": "生产完成即存草稿",
                                        "reason": "提前储备内容，避免断更风险",
                                        "completed": True
                                    },
                                    {
                                        "id": "account-verification",
                                        "time": "第6-7天",
                                        "action": "账号认证与权限开通",
                                        "content": "完成企业/个人认证，开通「商品目录」「薯条投放」权限",
                                        "example": "-",
                                        "publishTime": "平台审核期",
                                        "reason": "为后续流量投放和转化铺路",
                                        "completed": False
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "id": "week-2-3",
                        "title": "第2-3周：内容赛马与模型筛选（每日双更测试）",
                        "status": "process",
                        "tasks": [
                            {
                                "id": "daily-template",
                                "category": "每日执行模板（第8-21天）",
                                "completed": False,
                                "items": [
                                    {
                                        "id": "morning-content",
                                        "time": "早7:30-8:30",
                                        "action": "发布泛用户内容",
                                        "content": "萌宠/剧情视频",
                                        "example": "《月薪3千买的床垫，同事居然问我要链接》",
                                        "publishTime": "固定早高峰",
                                        "reason": "通勤时段用户活跃度高，适合吸睛内容",
                                        "completed": False
                                    },
                                    {
                                        "id": "evening-content",
                                        "time": "晚20:00-21:00",
                                        "action": "发布场景化内容",
                                        "content": "租房图文/测评",
                                        "example": "《房东床垫太烂？我花1000元换了张「会呼吸」的床垫》",
                                        "publishTime": "固定晚高峰",
                                        "reason": "睡前浏览黄金期，用户有耐心看干货",
                                        "completed": False
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "id": "growth",
                "title": "成长期",
                "subtitle": "第5-8周：粉丝增长与转化加速",
                "duration": "4周",
                "status": "wait",
                "icon": "LineChartOutlined",
                "color": "#52c41a",
                "progress": 0,
                "goal": "扩大曝光量，激活潜在用户，搭建转化路径",
                "weeks": [
                    {
                        "id": "week-5-6",
                        "title": "第5-6周：优化转化漏斗",
                        "status": "wait",
                        "tasks": [
                            {
                                "id": "conversion-optimization",
                                "category": "转化优化任务",
                                "completed": False,
                                "items": [
                                    {
                                        "id": "landing-page",
                                        "time": "第29-35天",
                                        "action": "搭建落地页",
                                        "content": "制作产品详情页，包含产品特点、用户评价、购买链接",
                                        "example": "「梦境床垫」专属落地页：舒适度测试+用户见证+限时优惠",
                                        "publishTime": "一周内完成",
                                        "reason": "提高转化率，规范化销售流程",
                                        "completed": False
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "id": "mature",
                "title": "成熟期",
                "subtitle": "第9-12周：精细化运营与品牌溢价",
                "duration": "4周",
                "status": "wait",
                "icon": "AimOutlined",
                "color": "#faad14",
                "progress": 0,
                "goal": "强化IP人设，沉淀私域用户，提升复购与溢价",
                "weeks": [
                    {
                        "id": "week-9-12",
                        "title": "第9-12周：品牌建设",
                        "status": "wait",
                        "tasks": [
                            {
                                "id": "brand-building",
                                "category": "品牌建设任务",
                                "completed": False,
                                "items": [
                                    {
                                        "id": "ip-development",
                                        "time": "第57-84天",
                                        "action": "IP形象打造",
                                        "content": "建立品牌故事，设计专属形象，制作系列内容",
                                        "example": "「睡眠专家小梦」IP形象：专业+亲切+可信赖",
                                        "publishTime": "持续进行",
                                        "reason": "建立品牌认知，提高用户粘性",
                                        "completed": False
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
        "created_at": "2025-06-10 12:50:14"
    }
    
    # 获取数据库连接
    db = next(get_db())
    sop_service = SOPService(db)
    
    try:
        # 导入SOP数据
        sop = sop_service.import_sop_from_json(sop_json_data)
        print(f"✅ SOP数据导入成功！SOP ID: {sop.id}")
        print(f"标题: {sop.title}")
        print(f"类型: {sop.type}")
        print(f"周期数: {len(sop.cycles)}")
        
        # 显示各周期信息
        for cycle in sop.cycles:
            print(f"  - {cycle.title} ({cycle.status})")
            for week in cycle.weeks:
                print(f"    - {week.title} ({week.status})")
                for task in week.tasks:
                    print(f"      - {task.category} (任务项: {len(task.items)})")
        
        return True
        
    except Exception as e:
        print(f"❌ SOP数据导入失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """主函数"""
    print("开始导入SOP数据...")
    success = import_sop_data()
    
    if success:
        print("\n🎉 SOP数据导入完成！")
        print("可以通过以下API访问：")
        print("- GET /api/sops/ - 获取SOP列表")
        print("- GET /api/sops/{sop_id} - 获取完整SOP数据")
        print("- PUT /api/sops/task-items/{item_id}/status - 更新任务项状态")
    else:
        print("\n❌ SOP数据导入失败，请检查错误信息")

if __name__ == "__main__":
    main() 