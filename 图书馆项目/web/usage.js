(()=>{
 const panel=el('div','usage-clock'),duration=el('span'),date=el('span');panel.hidden=true;panel.append(duration,date);document.querySelector('.heading').append(panel);
 let seconds=0,at=performance.now();
 function tick(){panel.hidden=!state;const minutes=Math.floor((seconds+(performance.now()-at)/1000)/60);duration.textContent=`累计 ${Math.floor(minutes/1440)}D ${Math.floor(minutes/60)%24}H ${minutes%60}M`;date.textContent=new Date().toLocaleString('zh-CN',{hour12:false});if(!panel.isConnected)document.querySelector('.heading').append(panel)}
 async function sync(){if(!bridge)return;const r=await call('usage');if(!r.error){seconds=r.seconds;at=performance.now();panel.title=r.error_message?'时长保存失败：'+r.error_message:'软件运行期间累计计时；每 5 分钟保存，正常退出时保存';tick()}}
 setInterval(tick,1000);setInterval(sync,10000);const startup=setInterval(()=>{if(bridge){clearInterval(startup);sync()}},150);
})();
