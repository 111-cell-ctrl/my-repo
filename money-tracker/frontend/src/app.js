// 登录状态检查
if (!localStorage.getItem('token') && 
    window.location.pathname !== '/login.html' && 
    window.location.pathname !== '/register.html') {
    window.location.href = '/login.html';
}

// 登录表单处理
if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            // 检查响应内容类型
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('收到非JSON响应:', text);
                alert('服务器响应格式错误，请检查后端服务是否正常运行');
                return;
            }

            const data = await response.json();
            if (response.ok) {
                localStorage.setItem('token', data.token);
                window.location.href = '/index.html';
            } else {
                alert('登录失败: ' + data.message);
            }
        } catch (error) {
            console.error('登录错误:', error);
            alert('网络错误: ' + error.message);
        }
    });
} 

// 注册表单处理
if (document.getElementById('registerForm')) {
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        // 输入为空验证
        if (!username || !password) {
            alert('用户名和密码不能为空！');
            return;
        }

        // 用户名长度验证
        if (username.length > 50) {
            alert('用户名长度不能超过 50 个字符！');
            return;
        }

        // 密码长度验证
        if (password.length < 6) {
            alert('密码长度不能少于 6 个字符！');
            return;
        }

        if (password !== confirmPassword) {
            alert('两次输入的密码不一致！');
            return;
        }

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            // 检查响应内容类型
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('收到非JSON响应:', text);
                alert('服务器响应格式错误，请检查后端服务是否正常运行');
                return;
            }

            const data = await response.json();
            if (response.ok) {
                alert('注册成功，请登录');
                window.location.href = '/login.html';
            } else {
                alert('注册失败: ' + data.message);
            }
        } catch (error) {
            console.error('注册错误:', error);
            alert('网络错误: ' + error.message);
        }
    });
} 

// 主页面逻辑
if (window.location.pathname === '/index.html') {
    const token = localStorage.getItem('token');

    // 加载记录
    async function loadRecords() {
        try {
            console.log('开始加载记录...');
            const response = await fetch('/api/records', {
                headers: { 'x-access-token': token }
            });

            console.log('记录请求响应状态:', response.status);

            if (response.ok) {
                // 检查响应内容类型
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    const text = await response.text();
                    console.error('收到非JSON响应:', text);
                    alert('服务器响应格式错误');
                    return;
                }

                const data = await response.json();
                console.log('收到记录数据:', data);
                
                const tableBody = document.getElementById('recordsTable');
                if (!tableBody) {
                    console.error('找不到记录表格元素');
                    return;
                }
                
                tableBody.innerHTML = '';

                let total = 0;

                if (data.records && Array.isArray(data.records)) {
                    data.records.forEach(record => {
                        const row = document.createElement('tr');
                        const recordDate = record.date ? new Date(record.date).toLocaleDateString('zh-CN') : '未知日期';
                        row.innerHTML = `
                            <td>${recordDate}</td>
                            <td>${record.category || '未知类别'}</td>
                            <td class="${record.amount >= 0 ? 'text-success' : 'text-danger'}">
                                ${record.amount >= 0 ? '+' : ''}${parseFloat(record.amount).toFixed(2)}
                            </td>
                            <td>${record.description || ''}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-danger delete-btn" data-record-id="${record.id}">
                                    删除
                                </button>
                            </td>
                        `;
                        tableBody.appendChild(row);
                        total += parseFloat(record.amount) || 0;
                    });
                    
                    // 为删除按钮添加事件监听器
                    document.querySelectorAll('.delete-btn').forEach(btn => {
                        btn.addEventListener('click', async (e) => {
                            const recordId = e.target.getAttribute('data-record-id');
                            if (confirm('确定要删除这条记录吗？')) {
                                await deleteRecord(recordId);
                            }
                        });
                    });
                }

                // 显示总计
                const totalElement = document.getElementById('totalAmount');
                if (totalElement) {
                    totalElement.textContent = total.toFixed(2);
                    totalElement.className = total >= 0 ? 'text-success fw-bold' : 'text-danger fw-bold';
                }
                
                console.log(`加载了 ${data.records ? data.records.length : 0} 条记录，总计: ${total.toFixed(2)}`);
            } else {
                console.error('记录请求失败:', response.status, response.statusText);
                if (response.status === 401) {
                    alert('登录已过期，请重新登录');
                    localStorage.removeItem('token');
                    window.location.href = '/login.html';
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    alert('加载记录失败: ' + (errorData.message || '未知错误'));
                }
            }
        } catch (error) {
            console.error('加载记录失败:', error);
            alert('加载记录失败，请检查网络连接: ' + error.message);
        }
    }

    // 添加记录
    if (document.getElementById('recordForm')) {
        document.getElementById('recordForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const amount = parseFloat(document.getElementById('amount').value);
            const category = document.getElementById('category').value;
            const description = document.getElementById('description').value;

            if (isNaN(amount)) {
                alert('请输入有效的金额');
                return;
            }

            try {
                const response = await fetch('/api/record', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'x-access-token': token
                    },
                    body: JSON.stringify({ amount, category, description })
                });

                if (response.ok) {
                    const data = await response.json();
                    alert('记录添加成功！');
                    document.getElementById('recordForm').reset();
                    loadRecords();
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    alert('添加失败: ' + (errorData.message || '未知错误'));
                }
            } catch (error) {
                alert('网络错误: ' + error.message);
            }
        });
    }

    // 登出功能
    if (document.getElementById('logoutBtn')) {
        document.getElementById('logoutBtn').addEventListener('click', () => {
            localStorage.removeItem('token');
            window.location.href = '/login.html';
        });
    }

    // 删除记录函数
    async function deleteRecord(recordId) {
        try {
            console.log('删除记录:', recordId);
            const response = await fetch(`/api/record/${recordId}`, {
                method: 'DELETE',
                headers: { 
                    'x-access-token': token
                }
            });

            if (response.ok) {
                const data = await response.json();
                console.log('删除成功:', data.message);
                alert('记录删除成功！');
                // 重新加载记录列表
                loadRecords();
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error('删除失败:', response.status, errorData);
                if (response.status === 401) {
                    alert('登录已过期，请重新登录');
                    localStorage.removeItem('token');
                    window.location.href = '/login.html';
                } else {
                    alert('删除失败: ' + (errorData.message || '未知错误'));
                }
            }
        } catch (error) {
            console.error('删除记录错误:', error);
            alert('删除失败，请检查网络连接: ' + error.message);
        }
    }

    // 初始加载
    loadRecords();
}