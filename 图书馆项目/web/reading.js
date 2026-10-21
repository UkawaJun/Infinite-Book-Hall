(()=>{
 // A single reusable ghost; never participates in shelf layout or hit testing.
 const ghost=document.createElement('img');ghost.id='reading-ghost';ghost.alt='';ghost.draggable=false;ghost.setAttribute('aria-hidden','true');ghost.hidden=true;document.body.append(ghost);
 let enabled=false,hovered=null,animation=null,timer=0,busy=null;
 const hd=new Map();
 function requestHD(node){clearTimeout(timer);timer=setTimeout(()=>{if(!enabled||hovered!==node||ghost.hidden||busy)return;const id=node.dataset.book;if(hd.has(id)){ghost.src=hd.get(id);return}busy=id;call('covers',{ids:[id],batch:'hd:'+id,hd:true}).then(r=>{if(r.error)busy=null})},80)}
 document.addEventListener('hd-cover',e=>{const {id,cover}=e.detail;busy=null;if(cover){hd.delete(id);hd.set(id,cover);if(hd.size>8)hd.delete(hd.keys().next().value);if(enabled&&hovered?.dataset.book===id&&!ghost.hidden)ghost.src=cover}if(enabled&&hovered&&hovered.dataset.book!==id)requestHD(hovered)});
 function hide(){clearTimeout(timer);animation?.cancel();animation=null;ghost.hidden=true;ghost.removeAttribute('src')}
 function reset(){enabled=false;hovered=null;hide();document.body.classList.remove('reading-mode')}
 function show(node){
  if(!enabled||currentShelf===null||!node?.isConnected)return hide();
  const source=node.querySelector('img');if(!source?.complete||!source.naturalWidth)return hide();
  hide();const rect=node.getBoundingClientRect(),area=pan.view.getBoundingClientRect();
  const h=Math.min(rect.height*1.12*2.5,Math.max(1,area.height-20)),w=Math.min(h*source.naturalWidth/source.naturalHeight,Math.max(1,area.width-20));
  const height=Math.min(h,w*source.naturalHeight/source.naturalWidth);
  const x=Math.max(area.left+10,Math.min(rect.left+(rect.width-w)/2,area.right-w-10));
  const y=Math.max(area.top+10,Math.min(rect.bottom-height-8,area.bottom-height-10));
  ghost.src=hd.get(node.dataset.book)||source.src;Object.assign(ghost.style,{left:x+'px',top:y+'px',width:w+'px',height:height+'px'});ghost.hidden=false;
  animation=ghost.animate([{transform:`translate(${rect.left-x}px,${rect.top-y}px) scale(${rect.width/w},${rect.height/height})`,opacity:0},{transform:'translate(0,0) scale(1)',opacity:.84}],{duration:130,easing:'cubic-bezier(.2,.7,.25,1)',fill:'forwards'});requestHD(node);
 }
 document.addEventListener('keydown',e=>{
  if(e.key.toLowerCase()!=='t'||e.repeat||e.ctrlKey||e.altKey||e.metaKey||e.isComposing||currentShelf===null||document.querySelector('dialog[open],.loading-mask')||e.target.closest?.('input,select,textarea,[contenteditable="true"]'))return;
  e.preventDefault();enabled=!enabled;document.body.classList.toggle('reading-mode',enabled);
  if(enabled){hovered=document.querySelector('.shelf-row .spine:hover')||hovered;show(hovered);toast('阅览模式已开启 · 悬停查看封面 · T 关闭')}else{hide();toast('阅览模式已关闭')}
 });
 document.addEventListener('pointerover',e=>{const node=e.target.closest?.('.shelf-row .spine');if(node&&node!==hovered){hovered=node;show(node)}});
 document.addEventListener('pointerout',e=>{if(hovered&&!hovered.contains(e.relatedTarget)){hovered=null;hide()}});
 document.addEventListener('pointerdown',hide,true);document.addEventListener('dragstart',hide,true);
 document.addEventListener('wheel',()=>{hovered=null;hide()},true);
 window.addEventListener('blur',hide);window.addEventListener('resize',hide);
 document.addEventListener('room-view-change',reset);
 new ResizeObserver(hide).observe($('scene'));
})();
