"""
专用的服务器启动脚本
确保在Windows上使用正确的事件循环策略
"""

import sys
import asyncio
import os

def setup_windows_event_loop():
    """设置Windows兼容的事件循环策略"""
    if sys.platform == "win32":
        print("🔧 检查Windows事件循环设置...")
        
        # 强制设置ProactorEventLoopPolicy
        policy = asyncio.WindowsProactorEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)
        
        # 验证设置
        current_policy = asyncio.get_event_loop_policy()
        policy_name = type(current_policy).__name__
        print(f"✅ 当前事件循环策略: {policy_name}")
        
        if isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
            print("✅ Windows Proactor事件循环策略设置成功")
            return True
        else:
            print(f"❌ 事件循环策略设置失败，当前为: {policy_name}")
            return False
    else:
        print("ℹ️ 非Windows平台，使用默认事件循环策略")
        return True

def test_subprocess_capability():
    """测试子进程创建能力"""
    if sys.platform != "win32":
        return True
    
    print("🧪 测试子进程创建能力...")
    
    async def test_subprocess():
        try:
            # 创建一个简单的子进程测试
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-c", "print('Subprocess test OK')",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print("✅ 子进程创建测试成功")
                return True
            else:
                print(f"❌ 子进程测试失败，返回码: {process.returncode}")
                print(f"错误输出: {stderr.decode()}")
                return False
                
        except NotImplementedError:
            print("❌ 子进程创建失败 - NotImplementedError")
            print("💡 当前事件循环不支持子进程，需要使用ProactorEventLoop")
            return False
        except Exception as e:
            print(f"❌ 子进程测试异常: {e}")
            return False
    
    # 运行测试
    try:
        return asyncio.run(test_subprocess())
    except Exception as e:
        print(f"❌ 运行子进程测试时出错: {e}")
        return False

def main():
    """主启动函数"""
    print("🚀 启动小红书多Agent自动化运营系统")
    print("=" * 50)
    
    # 1. 设置事件循环策略
    if not setup_windows_event_loop():
        print("💥 事件循环策略设置失败")
        sys.exit(1)
    
    # 2. 测试子进程能力
    if not test_subprocess_capability():
        print("💥 子进程创建测试失败")
        print("💡 这可能导致MCP连接问题")
        print("💡 建议检查事件循环设置")
        # 不退出，继续启动服务器
    
    print("=" * 50)
    print("🌟 预检查完成，启动Web服务器...")
    
    # 3. 导入并启动FastAPI应用
    try:
        # 确保当前目录在Python路径中
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # 导入主应用
        from main import app
        import uvicorn
        
        # 启动服务器
        print("🌐 启动Web服务器...")
        print("📍 访问地址: http://localhost:9000")
        print("🔧 MCP演示页面: http://localhost:9000/mcp-demo")
        print("🛠️ API文档: http://localhost:9000/docs")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=9000,
            log_level="info"
        )
        
    except Exception as e:
        print(f"💥 启动服务器时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 