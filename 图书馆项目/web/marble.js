/* Original subtle procedural marble shader. Concept reference: Foundry Wood Procedural,
   https://learn.foundry.com/modo/15.1/content/help/pages/shading_lighting/shader_items/wood.html
   No third-party shader source or remote runtime dependency. */
(()=>{const c=document.createElement('canvas');c.width=512;c.height=256;
const gl=c.getContext('webgl',{preserveDrawingBuffer:true});if(!gl)return;
const source=`precision mediump float;varying vec2 uv;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+1.),f.x),f.y);}
void main(){vec2 p=uv*4.;float f=noise(p)*.6+noise(p*2.1)*.25+noise(p*4.3)*.15;
float vein=pow(.5+.5*sin((p.x*.6+p.y*.35+f*1.1)*15.),22.);
vec3 stone=vec3(.94,.928,.90)-vec3(.05,.045,.038)*vein-vec3(.012)*f;
gl_FragColor=vec4(stone,1.);}`;
function compile(type,s){let sh=gl.createShader(type);gl.shaderSource(sh,s);gl.compileShader(sh);if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(sh));return sh}
try{let program=gl.createProgram();gl.attachShader(program,compile(gl.VERTEX_SHADER,'attribute vec2 pos;varying vec2 uv;void main(){uv=pos*.5+.5;gl_Position=vec4(pos,0.,1.);}'));gl.attachShader(program,compile(gl.FRAGMENT_SHADER,source));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))return;gl.useProgram(program);let buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);let loc=gl.getAttribLocation(program,'pos');gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);gl.viewport(0,0,512,256);gl.drawArrays(gl.TRIANGLES,0,6);window.marbleTexture=c.toDataURL()}catch(e){console.warn(e)}})();
