from crewai import Agent

def create_manager_agent(llm, role="project_manager"):
    """
    创建一个通用的 manager agent，英文 prompt，带中文注释
    """
    return Agent(
        role=role,  # 英文角色名
        goal=(
            # 英文描述
            "Coordinate all team members and ensure high-quality task completion. "
            "When delegating tasks, you must use the exact role name (e.g., 'chief_market_analyst'), "
            "and output the action input as a Python dict, not a string. "
            "Do not include any extra fields such as 'name', 'description', or 'args_schema'. "
            "Only output {'coworker': ..., 'task': ..., 'context': ...} format. "
            "For example: {'coworker': 'chief_market_analyst', 'task': 'analyze...', 'context': '...'}"
        ),
        # 中文注释：管理所有团队成员，分配任务时必须用英文角色名，输出格式为dict
        backstory="An experienced project manager skilled in planning and task assignment.",
        verbose=True,
        llm=llm,
        allow_delegation=True,
        delegation_config={
            "technique": "intent",
            "llm": llm,
            "prompt": (
                # 英文描述
                "When using the 'Delegate work to coworker' tool, the action input must be a Python dict "
                "containing only the following keys: 'coworker', 'task', 'context'. "
                "Do not output a string or include any extra fields. "
                "For example: {'coworker': 'chief_market_analyst', 'task': 'analyze...', 'context': '...'}"
            )
            # 中文注释：分配任务时，输入必须是只包含指定键的dict，不能有多余字段
        }
    ) 