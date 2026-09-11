-- 创建数据库
DROP DATABASE IF EXISTS tourism_system;
CREATE DATABASE tourism_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE tourism_system;

-- 景点信息表
CREATE TABLE attractions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    poi_id VARCHAR(50) UNIQUE NOT NULL COMMENT '景点ID',
    zone_name VARCHAR(100) COMMENT '景点区域',
    poi_name VARCHAR(200) NOT NULL COMMENT '景点名称',
    comment_count INT DEFAULT 0 COMMENT '评论数',
    comment_score DECIMAL(3,1) DEFAULT 0 COMMENT '评分',
    is_advertisement TINYINT(1) DEFAULT 0 COMMENT '是否广告',
    is_recommend TINYINT(1) DEFAULT 0 COMMENT '是否推荐',
    district_name VARCHAR(100) COMMENT '所在城市',
    cover_image_url TEXT COMMENT '封面图片URL',
    distance_str VARCHAR(50) COMMENT '距离中心距离',
    tag_list TEXT COMMENT '标签列表',
    detail_url TEXT COMMENT '详情页链接',
    market_price DECIMAL(10,2) COMMENT '市场价格',
    preferential_price DECIMAL(10,2) COMMENT '优惠价格',
    preferential_desc VARCHAR(200) COMMENT '优惠描述',
    price VARCHAR(50) COMMENT '价格',
    price_type VARCHAR(50) COMMENT '价格类型',
    price_type_desc VARCHAR(100) COMMENT '价格类型描述',
    is_free TINYINT(1) DEFAULT 0 COMMENT '是否免费',
    latitude DECIMAL(10,6) COMMENT '纬度',
    longitude DECIMAL(10,6) COMMENT '经度',
    heat_score INT DEFAULT 0 COMMENT '热度评分',
    city VARCHAR(50) COMMENT '城市',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_city (city),
    INDEX idx_score (comment_score),
    INDEX idx_heat (heat_score),
    INDEX idx_district (district_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='景点信息表';

-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    email VARCHAR(100) COMMENT '邮箱',
    role ENUM('admin', 'user') DEFAULT 'user' COMMENT '角色',
    avatar VARCHAR(255) COMMENT '头像',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    last_login TIMESTAMP NULL COMMENT '最后登录时间',
    status TINYINT(1) DEFAULT 1 COMMENT '状态 1启用 0禁用',
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 用户浏览历史表
CREATE TABLE user_browse_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    poi_id VARCHAR(50) NOT NULL COMMENT '景点ID',
    browse_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '浏览时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_poi_id (poi_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户浏览历史表';

-- 用户收藏表
CREATE TABLE user_favorites (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    poi_id VARCHAR(50) NOT NULL COMMENT '景点ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_poi (user_id, poi_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户收藏表';

-- 爬虫任务记录表
CREATE TABLE spider_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50) NOT NULL COMMENT '城市',
    page_num INT NOT NULL COMMENT '页码',
    status ENUM('pending', 'success', 'failed') DEFAULT 'pending' COMMENT '状态',
    crawl_date DATE NOT NULL COMMENT '爬取日期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_crawl_date (crawl_date),
    INDEX idx_city (city)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬虫任务记录表';

-- 系统日志表
CREATE TABLE system_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT COMMENT '用户ID',
    action VARCHAR(100) COMMENT '操作',
    ip VARCHAR(50) COMMENT 'IP地址',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统日志表';

-- -- 插入默认管理员账户 (密码: admin123)
-- INSERT INTO users (username, password, email, role) VALUES
-- ('admin', 'scrypt:32768:8:1$vZ8xK9YqF7gXjLmN$8f5e3a9c2b1d4e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f', 'admin@tourism.com', 'admin');
--
-- -- 插入测试用户 (密码: user123)
-- INSERT INTO users (username, password, email, role) VALUES
-- ('testuser', 'scrypt:32768:8:1$vZ8xK9YqF7gXjLmN$8f5e3a9c2b1d4e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f', 'user@tourism.com', 'user');
