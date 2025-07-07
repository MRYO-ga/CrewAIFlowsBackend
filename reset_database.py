#!/usr/bin/env python3
"""
重置数据库脚本
删除旧的数据库文件并重新创建表结构
"""

import os
import sys
import subprocess

def reset_database():
    """重置数据库"""
    print("🔄 开始重置数据库...")
    
    # 数据库文件路径
    db_path = "crewaiFlowsBackend/crewai_flows.db"
    backup_path = "crewaiFlowsBackend/crewai_flows.db.backup"
    
    try:
        # 1. 删除旧的数据库文件
        if os.path.exists(db_path):
            print(f"📝 删除旧数据库文件: {db_path}")
            os.remove(db_path)
            print("✅ 旧数据库文件已删除")
        else:
            print("📝 数据库文件不存在，跳过删除")
            
        # 2. 如果存在备份文件也删除
        if os.path.exists(backup_path):
            print(f"📝 删除备份文件: {backup_path}")
            os.remove(backup_path)
            print("✅ 备份文件已删除")
            
        # 3. 运行数据迁移脚本重新创建数据库
        print("🚀 重新创建数据库和数据...")
        
        # 切换到后端目录
        original_dir = os.getcwd()
        os.chdir("crewaiFlowsBackend")
        
        try:
            # 运行迁移脚本
            result = subprocess.run([
                sys.executable, 
                "run_migration.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 数据库重置完成！")
                print(result.stdout)
                return True
            else:
                print("❌ 数据库重置失败！")
                print("错误输出:", result.stderr)
                return False
                
        finally:
            # 恢复原目录
            os.chdir(original_dir)
            
    except Exception as e:
        print(f"❌ 重置数据库时出错: {e}")
        return False

def main():
    print("="*60)
    print("🔄 数据库重置工具")
    print("="*60)
    print()
    print("⚠️  重要提示:")
    print("1. 请先手动停止后端服务（关闭后端服务的命令行窗口）")
    print("2. 这将删除所有现有数据并重新创建")
    print("3. 重置完成后需要重新启动后端服务")
    print()
    
    # 确认操作
    response = input("确认要重置数据库吗？(输入 'yes' 确认): ")
    if response.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    # 执行重置
    if reset_database():
        print("\n" + "="*60)
        print("🎉 数据库重置成功！")
        print("="*60)
        print()
        print("📝 接下来的步骤:")
        print("1. 重新启动后端服务:")
        print("   cd crewaiFlowsBackend")
        print("   python main.py")
        print("2. 测试API接口:")
        print("   python test_api_simple.py")
        print("3. 访问API文档: http://localhost:9000/docs")
    else:
        print("\n❌ 数据库重置失败，请检查错误信息")

if __name__ == "__main__":
    main() 