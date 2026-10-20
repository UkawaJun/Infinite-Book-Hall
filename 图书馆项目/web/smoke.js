(async()=>{try{
 if(displayBookName('书'.repeat(51))!=='书'.repeat(50)+'…'||displayBookName('abcdefghijk\ufffd')!=='abcdefghij…'||displayBookName('普通书名.epub')!=='普通书名.epub')throw Error('book name truncation');
 await navigate('home');
 if(!document.querySelector('svg')||!document.querySelector('#pawn'))throw Error('maze / pawn missing');
 const original=state.player;
 const entry=state.entries.find(e=>e.available);
 if(entry){
   const target=state.layout.placements[entry.id],n=state.layout.size;
   const queue=[[state.player,[]]],seen=new Set([state.player]);let route;
   while(queue.length){const [cell,path]=queue.shift();if(cell===target){route=path;break}state.layout.walls[cell].forEach((wall,d)=>{let other=cell+[-n,1,n,-1][d];if(!wall&&!seen.has(other)){seen.add(other);queue.push([other,[...path,d]])}})}
   for(const d of route){const expected=state.player+[-n,1,n,-1][d];document.dispatchEvent(new KeyboardEvent('keydown',{key:['w','d','s','a'][d],bubbles:true}));for(let i=0;i<50&&state.player!==expected;i++)await new Promise(r=>setTimeout(r,20));if(state.player!==expected)throw Error('WASD failed')}
   await new Promise(r=>setTimeout(r,1000));
   const centerX=32+state.player%n*140+70,centerY=32+Math.floor(state.player/n)*140+108;
   if(Math.abs(pan.x+centerX*pan.scale-pan.view.clientWidth/2)>1||Math.abs(pan.y+centerY*pan.scale-pan.view.clientHeight/2)>1)throw Error('camera did not follow pawn '+JSON.stringify({x:pan.x,y:pan.y,cx:centerX,cy:centerY,scale:pan.scale,w:pan.view.clientWidth,h:pan.view.clientHeight,pawn:pawnVisual}));

   if(state.player!==target)throw Error('pawn movement failed');
   document.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));await new Promise(r=>setTimeout(r,500));
   if(state.mode==='shelves'){
     if(state.books.some(b=>b.cover))throw Error('overview must not render PDF covers');
     if(document.querySelectorAll('.mini-row').length!==state.shelf_count*6)throw Error('overview rows');
     document.body.dataset.capture='overview';await new Promise(r=>setTimeout(r,800));
     const loading=shelf(state,0);if(!document.querySelector('.loading-mask'))throw Error('progress overlay missing');await loading;
     if(document.querySelector('.loading-mask'))throw Error('progress overlay still visible');
     if(document.querySelectorAll('.shelf-row').length!==6)throw Error('shelf rows');
     const b=state.books.find(b=>b.shelf===0);if(b){
       pick(b);const drag=new DataTransfer();drag.setData('text/library-book',b.id);$('selection-panel').dispatchEvent(new DragEvent('drop',{dataTransfer:drag,bubbles:true,cancelable:true}));
       const node=document.querySelector('.spine'),row=node.parentElement;
       if(Math.abs(node.getBoundingClientRect().bottom-row.getBoundingClientRect().bottom)>1)throw Error('book must sit on shelf');
       const basketBefore=document.querySelector('.basket-book').getBoundingClientRect();pan.zoom(1.7);pan.x+=93;pan.y-=47;pan.apply();const saved=pan.snapshot();sizeBasketBooks();const stored=document.querySelector('.basket-book');if(!stored)throw Error('drag to basket failed');const sr=node.getBoundingClientRect(),br=stored.getBoundingClientRect();if(Math.abs(br.width-basketBefore.width)>1||Math.abs(br.height-basketBefore.height)>1)throw Error('basket changed with shelf zoom');if(Math.abs(br.width-($('basket').clientWidth-8))>1)throw Error('basket book does not fill basket width');
       await insertBook(b.id,b.shelf,b.row,b.id);
       if(JSON.stringify(saved)!==JSON.stringify(pan.snapshot()))throw Error('reorder changed camera');
       const readingBook=document.querySelector('.shelf-row .spine'),beforeReading=readingBook.getBoundingClientRect().toJSON();
       readingBook.dispatchEvent(new PointerEvent('pointerover',{bubbles:true}));
       document.dispatchEvent(new KeyboardEvent('keydown',{key:'t',bubbles:true}));
       const ghost=document.getElementById('reading-ghost');
       if(ghost.hidden||getComputedStyle(ghost).pointerEvents!=='none'||document.querySelectorAll('#reading-ghost').length!==1)throw Error('reading ghost missing or interactive');
       if(JSON.stringify(beforeReading)!==JSON.stringify(readingBook.getBoundingClientRect().toJSON()))throw Error('reading mode moved shelf book');
       document.dispatchEvent(new KeyboardEvent('keydown',{key:'t',bubbles:true}));if(!ghost.hidden)throw Error('reading ghost did not close');
       document.dispatchEvent(new KeyboardEvent('keydown',{key:'f',ctrlKey:true,bubbles:true}));const search=document.querySelector('.shelf-search'),query=search.querySelector('input');if(search.hidden)throw Error('search missing');query.value=b.name;query.dispatchEvent(new Event('input'));await new Promise(r=>setTimeout(r,160));if(!document.querySelector('.search-hit'))throw Error('search highlight missing');document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));if(!search.hidden||document.querySelector('.search-hit')||currentShelf===null)throw Error('search close changed shelf');


       const view=pan.view;const start=pan.snapshot();
       view.dispatchEvent(new PointerEvent('pointerdown',{button:0,clientX:50,clientY:50,bubbles:true}));view.dispatchEvent(new PointerEvent('pointermove',{clientX:80,clientY:90,bubbles:true}));view.dispatchEvent(new PointerEvent('pointerup',{bubbles:true}));
       if(JSON.stringify(start)!==JSON.stringify(pan.snapshot()))throw Error('left drag moved camera');
       view.dispatchEvent(new PointerEvent('pointerdown',{button:1,clientX:50,clientY:50,bubbles:true}));view.dispatchEvent(new PointerEvent('pointermove',{clientX:80,clientY:90,bubbles:true}));view.dispatchEvent(new PointerEvent('pointerup',{bubbles:true}));
       if(pan.x!==start.x+30||pan.y!==start.y+40)throw Error('middle drag failed');pan.restore(saved);

       if(!document.querySelector('.basket-book'))throw Error('basket missing');
       for(let i=0;i<60&&!covers.has(b.id);i++)await new Promise(r=>setTimeout(r,250));
       if(!covers.get(b.id))throw Error('async PDF cover missing');
       document.body.dataset.capture='shelf';await new Promise(r=>setTimeout(r,800));
     }
   }
 }
 document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));await new Promise(r=>setTimeout(r,200));if(currentShelf!==null)throw Error('ESC did not leave shelf');
 await navigate('home');document.body.dataset.test='ok';
}catch(e){document.body.dataset.test=String(e)}})();
