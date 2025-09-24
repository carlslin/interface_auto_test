#!/bin/bash
# 接口自动化测试框架 - Git上传脚本

echo "🚀 接口自动化测试框架 - Git上传脚本"
echo "=================================="

# 检查是否在正确的目录
if [ ! -f "README.md" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 检查Git状态
echo "📋 检查Git状态..."
git status

echo ""
echo "🔐 选择上传方式："
echo "1. 使用GitHub用户名和密码"
echo "2. 使用Personal Access Token"
echo "3. 使用SSH密钥"
echo "4. 显示详细指导"

read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "📤 使用用户名和密码上传..."
        git push origin main
        ;;
    2)
        echo "🔑 请输入您的Personal Access Token:"
        read -s token
        echo "📤 配置Token并上传..."
        git remote set-url origin https://carlslin:${token}@github.com/carlslin/interface_auto_test.git
        git push origin main
        ;;
    3)
        echo "🔑 配置SSH上传..."
        git remote set-url origin git@github.com:carlslin/interface_auto_test.git
        git push origin main
        ;;
    4)
        echo "📖 详细指导："
        echo ""
        echo "方法1 - 用户名和密码："
        echo "  git push origin main"
        echo "  输入用户名：carlslin"
        echo "  输入密码：您的GitHub密码或Personal Access Token"
        echo ""
        echo "方法2 - Personal Access Token："
        echo "  1. 访问 https://github.com/settings/tokens"
        echo "  2. 生成新的token，选择repo权限"
        echo "  3. 运行：git remote set-url origin https://carlslin:YOUR_TOKEN@github.com/carlslin/interface_auto_test.git"
        echo "  4. 运行：git push origin main"
        echo ""
        echo "方法3 - SSH密钥："
        echo "  1. 生成SSH密钥：ssh-keygen -t ed25519 -C \"your.email@example.com\""
        echo "  2. 添加公钥到GitHub：https://github.com/settings/keys"
        echo "  3. 运行：git remote set-url origin git@github.com:carlslin/interface_auto_test.git"
        echo "  4. 运行：git push origin main"
        echo ""
        echo "方法4 - Web界面上传："
        echo "  1. 访问 https://github.com/carlslin/interface_auto_test"
        echo "  2. 点击 \"Add file\" → \"Upload files\""
        echo "  3. 拖拽所有项目文件"
        echo "  4. 提交信息：🎉 接口自动化测试框架完整版"
        echo "  5. 点击 \"Commit changes\""
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 上传完成！"
echo "🌐 查看仓库：https://github.com/carlslin/interface_auto_test"
echo ""
echo "📋 项目信息："
echo "  - 仓库地址：https://github.com/carlslin/interface_auto_test"
echo "  - 主要分支：main"
echo "  - 最新提交：🎉 接口自动化测试框架完整版"
echo "  - 文件数量：74个文件"
echo "  - 代码行数：27,209行新增代码"
