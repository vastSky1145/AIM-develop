"""
API测试脚本
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

def test_login(username="sxs", password="123456"):
    """测试登录"""
    print("\n=== 测试登录 ===")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": username, "password": password}
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if data.get("success"):
        token = data["data"]["token"]
        print(f"\n获取到Token: {token[:50]}...")
        return token
    return None

def test_get_papers(token):
    """测试获取论文列表"""
    print("\n=== 测试获取论文列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/papers/list",
        headers=headers
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"论文数量: {len(data.get('data', []))}")
    if data.get("data"):
        print(f"第一篇论文标题: {data['data'][0].get('paper_title')}")

def test_knowledge_search(token, query="video streaming"):
    """测试知识库检索"""
    print(f"\n=== 测试知识库检索: '{query}' ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/knowledge/search",
        headers=headers,
        json={"query": query, "k": 3}
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    if data.get("success"):
        docs = data["data"]["documents"]
        print(f"找到{len(docs)}个结果")
        if docs:
            print(f"第一个结果: {docs[0]['content'][:100]}...")

def test_get_prompt(token, ppt_id="ppt1.1"):
    """测试获取Prompt模板"""
    print(f"\n=== 测试获取Prompt模板: {ppt_id} ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/prompts/get/{ppt_id}",
        headers=headers
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    if data.get("success"):
        prompt = data["data"]["prompt_json"]
        print(f"模板长度: {len(prompt)} 字符")
        print(f"模板预览: {prompt[:150]}...")

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始API测试")
    print("=" * 60)
    
    # 1. 健康检查
    test_health()
    
    # 2. 登录
    token = test_login()
    if not token:
        print("\n❌ 登录失败，终止测试")
        return
    
    # 3. 获取论文列表
    test_get_papers(token)
    
    # 4. 知识库检索
    test_knowledge_search(token)
    
    # 5. 获取Prompt模板
    test_get_prompt(token)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()

