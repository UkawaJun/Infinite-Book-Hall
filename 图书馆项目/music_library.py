import shutil
from pathlib import Path
from PyQt6.QtCore import QUrl, QEventLoop, QTimer
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtWidgets import QFileDialog

def handle(bridge, action, data):
    root=bridge.file.parent/'music';root.mkdir(exist_ok=True)
    if action=='music_import':
        name,_=QFileDialog.getOpenFileName(bridge.window,'导入音乐（至少 30 秒）','','音频 (*.mp3 *.wav *.ogg *.flac *.m4a *.aac)')
        if name:
            player=QMediaPlayer();loop=QEventLoop()
            player.durationChanged.connect(lambda d: loop.quit() if d>0 else None)
            player.errorOccurred.connect(lambda *args: loop.quit())
            player.setSource(QUrl.fromLocalFile(name));QTimer.singleShot(10000,loop.quit)
            if not player.duration():loop.exec()
            duration=player.duration();player.setSource(QUrl())
            if duration<30000:raise ValueError('导入失败：音频必须至少 30 秒，且能识别其时长')
            dest=root/Path(name).name
            if dest.exists():raise ValueError('同名歌曲已存在，请先改名或删除旧歌曲')
            shutil.copy2(name,dest)
    elif action=='music_delete':
        name=data['name']
        if Path(name).name!=name:raise ValueError('无效歌曲名称')
        (root/name).unlink()
    elif action=='music_settings':
        bridge.cfg['music']={'volume':max(0,min(1,float(data['volume']))),'auto':bool(data['auto'])};bridge.save()
    return {'tracks':[{'name':p.name,'url':QUrl.fromLocalFile(str(p)).toString()} for p in sorted(root.iterdir()) if p.is_file() and p.suffix.lower() in ('.mp3','.wav','.ogg','.flac','.m4a','.aac')], 'settings':bridge.cfg.get('music',{'auto':True,'volume':.4})}
