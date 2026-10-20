# 木纹材质参考

书架使用 web/wood.js 的原创 GLSL 程序化木纹着色器，在本地 WebGL 中实时计算纹理并作为共享材质使用。纹理生成后重复使用，不持续运行无意义的动画；无 WebGL 时退回 CSS 木纹。

木纹概念参考（年轮颜色、扰动、细纹）：
https://learn.foundry.com/modo/15.1/content/help/pages/shading_lighting/shader_items/wood.html

未复制第三方 shader 源码，没有外部图片许可或联网加载依赖。
