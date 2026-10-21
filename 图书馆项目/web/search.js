(()=>{
 const panel=el('div','shelf-search'),input=el('input'),count=el('span'),close=el('button','','关闭 ×');panel.hidden=true;input.type='search';input.placeholder='搜索当前书架的书名';input.setAttribute('aria-label','搜索当前书架');panel.append(input,count,close);document.body.append(panel);let timer=0,names=new Map();
 function filter(){const query=input.value.trim().normalize('NFKC').toLocaleLowerCase();let hits=0;document.querySelectorAll('.shelf-row .spine').forEach(node=>{const hit=!!query&&(names.get(node.dataset.book)||'').includes(query);node.classList.toggle('search-hit',hit);if(hit)hits++});count.textContent=query?`${hits} 本匹配`:'输入书名搜索'}
 function hide(){clearTimeout(timer);panel.hidden=true;input.value='';document.querySelectorAll('.search-hit').forEach(node=>node.classList.remove('search-hit'));input.blur()}
 close.onclick=hide;input.oninput=()=>{clearTimeout(timer);timer=setTimeout(filter,100)};
 document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&!panel.hidden){e.preventDefault();e.stopImmediatePropagation();hide();return}
  if(e.ctrlKey&&e.key.toLowerCase()==='f'&&currentShelf!==null&&!document.querySelector('dialog[open],.loading-mask')){e.preventDefault();e.stopImmediatePropagation();names=new Map((state?.books||[]).filter(b=>b.shelf===currentShelf).map(b=>[b.id,b.name.normalize('NFKC').toLocaleLowerCase()]));panel.hidden=false;filter();input.focus();input.select()}
 },true);
 document.addEventListener('room-view-change',hide);
})();
