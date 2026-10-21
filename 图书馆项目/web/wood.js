/* Original procedural wood shader. Concept reference: Foundry Wood Procedural,
   https://learn.foundry.com/modo/15.1/content/help/pages/shading_lighting/shader_items/wood.html
   No third-party shader source or remote runtime dependency. */
(()=>{const c=document.createElement('canvas');c.width=512;c.height=256;
const gl=c.getContext('webgl',{preserveDrawingBuffer:true});if(!gl)return;
const source=`precision mediump float;varying vec2 uv;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+1.),f.x),f.y);}
void main(){vec2 p=uv*vec2(3.,16.);float warp=noise(p*.65)*2.+noise(p*1.7)*.35;
float rings=.5+.5*sin((p.y+warp)*17.);float fine=noise(uv*vec2(32.,230.));
vec3 light=vec3(.60,.40,.22),dark=vec3(.27,.14,.065);vec3 wood=mix(light,dark,pow(rings,5.)*.55+fine*.21);
gl_FragColor=vec4(wood,1.);}`;
function compile(type,s){let sh=gl.createShader(type);gl.shaderSource(sh,s);gl.compileShader(sh);if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(sh));return sh}
try{let program=gl.createProgram();gl.attachShader(program,compile(gl.VERTEX_SHADER,'attribute vec2 pos;varying vec2 uv;void main(){uv=pos*.5+.5;gl_Position=vec4(pos,0.,1.);}'));gl.attachShader(program,compile(gl.FRAGMENT_SHADER,source));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))return;gl.useProgram(program);let buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);let loc=gl.getAttribLocation(program,'pos');gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);gl.viewport(0,0,512,256);gl.drawArrays(gl.TRIANGLES,0,6);document.documentElement.style.setProperty('--wood',`url("${c.toDataURL()}")`)}catch(e){console.warn(e)}})();
