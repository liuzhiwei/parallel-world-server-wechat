# 数字分身API文档

## 接口概述

本文档描述了数字分身系统的两个主要API接口。

## 1. 头像上传接口

### 接口信息
- **URL**: `POST /api/upload`
- **Content-Type**: `multipart/form-data`

### 请求参数
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| file | File | 是 | 上传的图片文件 |
| type | String | 是 | 上传类型，必须为 "avatar" |

### 支持的图片格式
- PNG
- JPG/JPEG
- GIF
- WebP

### 响应格式
```json
{
  "code": 0,
  "data": {
    "url": "/uploads/avatars/uuid-filename.ext"
  },
  "message": "success"
}
```

### 错误响应
```json
{
  "code": -1,
  "data": null,
  "message": "错误信息"
}
```

### 使用示例
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('type', 'avatar');

fetch('/api/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  if (data.code === 0) {
    console.log('上传成功:', data.data.url);
  } else {
    console.error('上传失败:', data.message);
  }
});
```

## 2. 创建数字分身接口

### 接口信息
- **URL**: `POST /api/profile`
- **Content-Type**: `application/json`

### 请求参数
| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| user_id | String | 是 | 用户ID |
| name | String | 是 | 分身名称 |
| description | String | 是 | 性格描述 |
| avatar_url | String | 是 | 头像URL（来自上传接口） |

### 响应格式
```json
{
  "code": 0,
  "data": {
    "ok": true,
    "message": "分身创建成功",
    "avatar": {
      "id": 1,
      "user_id": "user123",
      "name": "我的数字分身",
      "description": "一个友善、聪明的AI助手",
      "avatar_url": "/uploads/avatars/uuid-filename.png",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  },
  "message": "success"
}
```

### 使用示例
```javascript
const profileData = {
  user_id: "user123",
  name: "我的数字分身",
  description: "一个友善、聪明的AI助手，喜欢帮助用户解决问题",
  avatar_url: "/uploads/avatars/uuid-filename.png"
};

fetch('/api/profile', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(profileData)
})
.then(response => response.json())
.then(data => {
  if (data.code === 0) {
    console.log('分身创建成功:', data.data.avatar);
  } else {
    console.error('创建失败:', data.message);
  }
});
```

## 错误码说明

| 错误码 | 描述 |
|--------|------|
| 0 | 成功 |
| -1 | 失败 |

## 注意事项

1. **文件上传限制**: 目前只支持图片格式，文件大小建议不超过10MB
2. **用户ID唯一性**: 每个用户ID只能创建一个数字分身，重复创建会更新现有分身
3. **文件存储**: 上传的文件存储在 `uploads/avatars/` 目录下
4. **安全性**: 文件名会自动生成UUID，避免文件名冲突和安全问题

## 测试

可以使用提供的 `test_avatar_api.py` 脚本进行接口测试：

```bash
python test_avatar_api.py
```

确保服务器运行在 `http://127.0.0.1:5000`，或修改脚本中的 `BASE_URL` 变量。
