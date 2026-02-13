const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('serviceApi', {
    addService: () => ipcRenderer.invoke('run:add_service'),
    getIp: () => ipcRenderer.invoke('run:get_ip'),
    deleteService: () => ipcRenderer.invoke('run:delete_service'),
    restartService: () => ipcRenderer.invoke('run:restart_service'),
});
