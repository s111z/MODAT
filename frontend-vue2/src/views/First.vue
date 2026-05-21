<template>
  <div class="mota-container">
    <div class="logo-container">
        <div class="logo-icon">
            <img src="@/assets/images/logo.png" alt="Mota Logo" class="logo-image" />
        </div>
        <img src="@/assets/images/title.png" class="logo-text"/>
    </div>

    <div class="main-content">
      
      <img src="@/assets/images/title.png" class="main-title"/>
      <div class="button-container">
        <div class="btn" @click="navigateTo('/content')">进入 mota</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'First',
  methods: {
    // 使用 Vue 2 原生的路由跳转方式，并增加防呆判断，避免重复点击报错
    navigateTo(path) {
      if (this.$route.path !== path) {
        this.$router.push(path);
      }
    }
  }
}
</script>
<style scoped>
/* 容器全屏，引入背景图 */
.mota-container {
  width: 100%;
  height: 100vh;
  font-family: 'Times New Roman', 'PingFang SC', 'Microsoft YaHei', serif;
  background-image: url('@/assets/images/first_backgroud.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
}

/* 1. 左上角 Logo 区域：等比例放大 */
.logo-container {
  position: absolute;
  top: 10px;
  left: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 70px;
  height: 70px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%; 
  overflow: hidden; 
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain; 
}

.logo-text {
  font-size: 54px;
  font-weight: 900;
  color: #000;
  letter-spacing: -2px;
  width: 150px;
  height: 36px;
}

/* 2. 画面中央核心内容区：为了给底部留白，整体稍微偏上 */
.main-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 250px; /* 使用 vh 保证在不同屏幕高度下都能处于黄金偏上位置 */
}

/* 3. 主标题：极限放大，字间距极致收紧 */
.main-title {
  font-size: 160px; /* 字体放大一倍以上 */
  font-weight: 900;
  color: #000;
  margin: 0;
  letter-spacing: -18px; /* 紧凑感来源 */
  line-height: 0.75;
  width: 480px;
  height: 120px;
}

/* 4. 按钮容器：紧贴标题下方 */
.button-container {
  display: flex;
  margin-top: 40px;
  margin-bottom: 40px; /* 让底部的叶片/微笑能微微嵌入按钮下方 */
  z-index: 2; 
}

/* 5. 拟物感按钮：化身巨大的扁平圆角矩形 */
.btn {
  width: 400px; /* 宽度大幅拉长 */
  height: 120px; /* 高度加厚 */
  background: linear-gradient(135deg, rgba(232, 208, 170, 0) 0%, rgba(228, 200, 158, 0) 100%);
  border-radius: 12px;
  /* 多层阴影增强立体感 */
  box-shadow:
    0 4px 8px rgba(122, 104, 80, 0.1),
    0 8px 16px rgba(122, 104, 80, 0.15),
    0 16px 32px rgba(122, 104, 80, 0.2),
    0 24px 48px rgba(122, 104, 80, 0.15),
    inset 0 3px 6px rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.3s ease;
  backdrop-filter: blur(10px);

  /* 文字居中显示 */
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 26px;
  font-weight: bold;
  color: #7a6850;
  letter-spacing: 2px;
}

.btn:hover {
  transform: translateY(-4px);
  background: linear-gradient(135deg, rgba(236, 217, 184, 0.9) 0%, rgba(232, 207, 172, 0) 100%);
  box-shadow:
    0 6px 12px rgba(122, 104, 80, 0.15),
    0 12px 24px rgba(122, 104, 80, 0.2),
    0 20px 40px rgba(122, 104, 80, 0.25),
    0 32px 64px rgba(122, 104, 80, 0.2),
    inset 0 3px 6px rgba(255, 255, 255, 0.95);
  color: #5c4e3b;
}

.btn:active {
  transform: translateY(-2px);
  background: linear-gradient(135deg, rgba(228, 200, 158, 0.95) 0%, rgba(223, 193, 146, 0.95) 100%);
  box-shadow:
    0 3px 6px rgba(122, 104, 80, 0.15),
    0 6px 12px rgba(122, 104, 80, 0.2),
    0 12px 24px rgba(122, 104, 80, 0.25),
    inset 0 2px 4px rgba(255, 255, 255, 0.85);
  color: #4a3a28;
}

/* 底部微笑/叶片装饰区 */
.smile-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}

/* 6. SVG 弧形：宽度超越两个按钮的总和 */
.smile-svg {
  width: 1000px; /* 覆盖整个中心区域的宽度 */
  height: auto;
  filter: drop-shadow(0px 15px 12px rgba(180, 100, 50, 0.35));
}

/* 7. 底部光晕：随着 SVG 的变大而大面积铺开 */
.smile-shadow {
  width: 600px;
  height: 50px;
  background: rgba(190, 110, 40, 0.3);
  border-radius: 50%;
  filter: blur(28px);
  margin-top: -10px; /* 向上偏移，融入弧形底部 */
}
</style>
