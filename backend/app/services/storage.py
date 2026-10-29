import os, uuid
from pathlib import Path
class LocalStorage:
    def __init__(self):
        self.root=Path(os.getenv('UPLOAD_DIR','./uploads'))
        self.root.mkdir(parents=True,exist_ok=True)
    def save(self,image):
        key=f'{uuid.uuid4().hex}.jpg'
        image.save(self.root/key,'JPEG',quality=90)
        return key
    def path(self,key):
        path=(self.root/key).resolve()
        if path.parent!=self.root.resolve(): raise ValueError('Invalid storage key')
        return path
    def delete(self,key): self.path(key).unlink(missing_ok=True)
storage=LocalStorage()
