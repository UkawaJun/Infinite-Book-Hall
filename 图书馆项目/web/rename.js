function requestRename(book){
 const dialog=el('dialog','rename-dialog'),heading=el('h3','','修改书名'),input=el('input'),error=el('p','rename-error'),buttons=el('div','actions'),cancel=el('button','','取消'),save=el('button','','保存名称');
 input.value=book.name;input.setAttribute('aria-label','新的书籍文件名');cancel.onclick=()=>dialog.close();
 save.onclick=async()=>{save.disabled=true;error.textContent='';const result=await call('rename',{id:book.id,name:input.value});save.disabled=false;
 if(result.error){error.textContent='改名失败：'+result.error;return}
 const view=pan?.snapshot(),shown=currentShelf;
 const oldCover=covers.get(result.old_id);if(oldCover)covers.set(result.new_id,oldCover);
 const renamed=result.book||result.state.books?.find(b=>b.id===result.new_id);
 if(basket.has(result.old_id)){const old=basket.get(result.old_id);basket.delete(result.old_id);basket.set(result.new_id,{...old,...renamed,id:result.new_id,cover:oldCover})}
 state=result.state;dialog.close();
 if(shown!==null){currentShelf=shown;drawShelf(state,Math.min(shown,state.shelf_count-1),view)}else{render(state);if(view)pan.restore(view)}
 drawBasket();if(renamed)pick(renamed);
 };
 input.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();save.click()}};buttons.append(cancel,save);dialog.append(heading,input,error,buttons);dialog.addEventListener('close',()=>dialog.remove());document.body.append(dialog);dialog.showModal();input.focus();input.select();
}
