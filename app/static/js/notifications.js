// WebSocket bağlantısı ve bildirim yönetimi
document.addEventListener('DOMContentLoaded', () => {
    // Socket.io configuration with reconnection settings
    const socket = io({
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        reconnectionAttempts: 5
    });

    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;

    // Bağlantı durumu
    socket.on('connect', () => {
        console.log('WebSocket bağlantısı kuruldu');
        reconnectAttempts = 0;
        showNotification('Connection restored', 'success');
        // Remove any existing connection error messages
        const errorBanner = document.getElementById('connection-error');
        if (errorBanner) {
            errorBanner.remove();
        }
    });

    socket.on('disconnect', () => {
        console.log('WebSocket bağlantısı kesildi');
        showConnectionError();
    });

    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        reconnectAttempts++;
        if (reconnectAttempts >= maxReconnectAttempts) {
            showNotification('Unable to connect to server. Please refresh the page.', 'danger');
        }
    });

    // Envanter güncelleme bildirimleri
    socket.on('inventory_update', (data) => {
        try {
            const { product_id, action, data: productData, user } = data;
            const message = getInventoryMessage(action, productData, user);
            showNotification(message, action === 'delete' ? 'warning' : 'info');
            
            if (action === 'delete' || action === 'transfer') {
                setTimeout(() => location.reload(), 2000);
            }
        } catch (error) {
            console.error('Error handling inventory update:', error);
        }
    });

    // Stok uyarıları
    socket.on('stock_alert', (data) => {
        try {
            const { product_name, lab_code, level, quantity, minimum } = data;
            
            let message = '';
            let type = 'warning';
            
            if (level === 'out') {
                message = `${lab_code}: "${product_name}" stokta TÜKENDİ!`;
                type = 'danger';
            } else if (level === 'low') {
                message = `${lab_code}: "${product_name}" minimum stok seviyesinin altında! (${quantity}/${minimum})`;
            }
            
            showNotification(message, type);
        } catch (error) {
            console.error('Error handling stock alert:', error);
        }
    });
});

// Bildirim yardımcı fonksiyonları
function getInventoryMessage(action, data, user) {
    switch (action) {
        case 'add':
            return `${user}: Yeni ürün eklendi - "${data.name}"`;
        case 'edit':
            return `${user}: Ürün güncellendi - "${data.name}"`;
        case 'delete':
            return `${user}: Ürün silindi - "${data.name}"`;
        case 'transfer':
            return `${user}: Ürün transfer edildi - "${data.name}"`;
        default:
            return `Envanter güncellendi`;
    }
}

function showNotification(message, type = 'info') {
    // Bootstrap toast kullanarak bildirim göster
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        createToastContainer();
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                    data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // 5 saniye sonra toast'ı kaldır
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1050';
    document.body.appendChild(container);
}

function showConnectionError() {
    // Only show one error banner at a time
    if (document.getElementById('connection-error')) {
        return;
    }

    const errorDiv = document.createElement('div');
    errorDiv.id = 'connection-error';
    errorDiv.className = 'alert alert-warning alert-dismissible fade show fixed-top mx-auto mt-3';
    errorDiv.style.maxWidth = '500px';
    errorDiv.style.zIndex = '1100';
    errorDiv.innerHTML = `
        <strong>Connection Lost</strong>
        <span class="ms-2">Attempting to reconnect...</span>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(errorDiv);
}