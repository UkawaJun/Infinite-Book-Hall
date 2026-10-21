class PanZoom{
 constructor(view,world,width,height){this.view=view;this.world=world;this.width=width;this.height=height;this.fit();
 view.addEventListener('wheel',e=>{e.preventDefault();document.dispatchEvent(new Event('manual-camera'));const r=view.getBoundingClientRect();this.zoom(Math.exp(-e.deltaY*.0015),e.clientX-r.left,e.clientY-r.top)},{passive:false});
 let drag=null,moved=false;
 view.addEventListener('auxclick',e=>{if(e.button===1)e.preventDefault()});
 view.addEventListener('pointerdown',e=>{if(e.button!==1)return;e.preventDefault();document.dispatchEvent(new Event('manual-camera'));drag={x:e.clientX,y:e.clientY,ox:this.x,oy:this.y};moved=false});
 view.addEventListener('pointermove',e=>{if(!drag)return;let dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>4){moved=true;try{view.setPointerCapture(e.pointerId)}catch(_){}}this.x=drag.ox+dx;this.y=drag.oy+dy;this.apply()});
 view.addEventListener('pointerup',()=>{drag=null});view.addEventListener('pointercancel',()=>{drag=null});
 view.addEventListener('click',e=>{if(moved){e.preventDefault();e.stopPropagation();moved=false}},true);
 }
 snapshot(){return {scale:this.scale,x:this.x,y:this.y}}
 restore(v){this.scale=v.scale;this.x=v.x;this.y=v.y;this.apply()}
 fit(){this.scale=Math.min(1,(this.view.clientWidth-32)/this.width,(this.view.clientHeight-32)/this.height);this.scale=Math.max(.15,this.scale);this.x=(this.view.clientWidth-this.width*this.scale)/2;this.y=(this.view.clientHeight-this.height*this.scale)/2;this.apply()}
 apply(){this.world.style.transform=`translate(${this.x}px,${this.y}px) scale(${this.scale})`;if(this.label)this.label.textContent=Math.round(this.scale*100)+'%'}
 zoom(factor,cx=this.view.clientWidth/2,cy=this.view.clientHeight/2){let next=Math.max(.15,Math.min(4,this.scale*factor));let ratio=next/this.scale;this.x=cx-(cx-this.x)*ratio;this.y=cy-(cy-this.y)*ratio;this.scale=next;this.apply()}
}
