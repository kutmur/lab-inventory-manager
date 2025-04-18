// WebSocket bağlantısı ve bildirim yönetimi
document.addEventListener('DOMContentLoaded', () => {
    // Socket.io bağlantısı
    const socket = io();

    // Bağlantı durumu
    socket.on('connect', () => {
        console.log('WebSocket bağlantısı kuruldu');
    });

    socket.on('disconnect', () => {
        console.log('WebSocket bağlantısı kesildi');
    });

    // Envanter güncelleme bildirimleri
    socket.on('inventory_update', (data) => {
        const { product_id, action, data: productData, user } = data;
        
        // Toast notification göster
        const message = getInventoryMessage(action, productData, user);
        showNotification(message, action === 'delete' ? 'warning' : 'info');
        
        // Sayfayı yenile (isteğe bağlı)
        if (action === 'delete' || action === 'transfer') {
            setTimeout(() => location.reload(), 2000);
        }
    });

    // Stok uyarıları
    socket.on('stock_alert', (data) => {
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