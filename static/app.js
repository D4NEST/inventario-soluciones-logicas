// ====================================================================
// CONFIGURACIÓN SEGURA - USAR MISMO DOMINIO
// ====================================================================
const API_BASE_URL = window.location.origin;
const AUTH_URL = `${API_BASE_URL}/api/auth`;
const INVENTARIO_URL = `${API_BASE_URL}/api/inventario`;

console.log("🚀 Sistema de inventario inicializando...");
console.log("🌐 API Base URL:", API_BASE_URL);

// ====================================================================
// ELEMENTOS DEL DOM - ACTUALIZADOS Y VERIFICADOS
// ====================================================================
const loginScreen = document.getElementById("loginScreen");
const dashboardScreen = document.getElementById("dashboardScreen");
const loginForm = document.getElementById("loginForm");
const loginError = document.getElementById("loginError");
const logoutBtn = document.getElementById("logoutBtn");
const userName = document.getElementById("userName");
const userInitial = document.getElementById("userInitial");

const inventoryTableBody = document.getElementById("inventoryTableBody");
const totalItems = document.getElementById("totalItems");
const lowStockItems = document.getElementById("lowStockItems");
const totalValue = document.getElementById("totalValue");

// Elementos para seriales
const componentTypeSelect = document.getElementById("componentType");
const serialProductSelect = document.getElementById("serialProduct");
const serialCode = document.getElementById("serialCode");
const serialForm = document.getElementById("serialForm");
const serialMessage = document.getElementById("serialMessage");

// Elementos para productos
const addProductBtn = document.getElementById("addProductBtn");
const productModal = document.getElementById("productModal");
const closeProductModal = document.getElementById("closeProductModal");
const productForm = document.getElementById("productForm");
const productMessage = document.getElementById("productMessage");
const productTypeSelect = document.getElementById("productTypeSelect"); // ✅ CORREGIDO
const productNameInput = document.getElementById("productName");
const productSKUInput = document.getElementById("productSKU");
const productDescription = document.getElementById("productDescription");

// Elementos para crear nueva categoría
const categoryModal = document.getElementById("categoryModal");
const closeCategoryModal = document.getElementById("closeCategoryModal");
const categoryForm = document.getElementById("categoryForm");
const categoryMessage = document.getElementById("categoryMessage");
const categoryNameInput = document.getElementById("categoryName");
const addNewCategoryBtn = document.getElementById("addNewCategoryBtn");
const newCategoryBtn = document.getElementById("newCategoryBtn"); // ✅ BOTÓN ALTERNATIVO

// Elementos comunes
const addItemBtn = document.getElementById("addItemBtn");
const itemModal = document.getElementById("itemModal");
const closeModal = document.getElementById("closeModal");
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");

// Elementos para gestión de seriales
const serialsDetailModal = document.getElementById("serialsDetailModal");
const closeSerialsModal = document.getElementById("closeSerialsModal");
const serialsModalTitle = document.getElementById("serialsModalTitle");
const serialsTableBody = document.getElementById("serialsTableBody");

// Nuevos elementos para cambio de estado
const changeStatusModal = document.getElementById("changeStatusModal");
const closeStatusModal = document.getElementById("closeStatusModal");
const newStatusSelect = document.getElementById("newStatus");
const statusNotes = document.getElementById("statusNotes");
const confirmStatusChange = document.getElementById("confirmStatusChange");
const cancelStatusChange = document.getElementById("cancelStatusChange");
const statusMessage = document.getElementById("statusMessage");

// Botones de acciones rápidas
const btnMarcarInstalados = document.getElementById("btnMarcarInstalados");
const btnMarcarDanados = document.getElementById("btnMarcarDanados");
const btnMarcarRetirados = document.getElementById("btnMarcarRetirados");

// ====================================================================
// VARIABLES GLOBALES OPTIMIZADAS
// ====================================================================
let currentUser = null;
let ALL_PRODUCT_MODELS = [];
let productTypesCache = null;
let inventoryCache = null;
let sessionCheckerInterval = null;
let currentProductId = null;
let currentSerialId = null;
let selectedSerials = new Set();

// ====================================================================
// VERIFICACIÓN DE ELEMENTOS DOM
// ====================================================================
function verificarElementosDOM() {
    console.log("🔍 Verificando elementos DOM críticos:");
    
    const elementos = {
        loginScreen,
        dashboardScreen,
        loginForm,
        productTypeSelect,
        productModal,
        categoryModal,
        addProductBtn,
        newCategoryBtn,
         // addNewCategoryBtn,  //
        itemModal,
        serialsDetailModal
    };
    
    let todosExisten = true;
    for (const [nombre, elemento] of Object.entries(elementos)) {
        if (!elemento) {
            console.error(`❌ Elemento no encontrado: ${nombre}`);
            todosExisten = false;
        } else {
            console.log(`✅ ${nombre}: OK`);
        }
    }
    
    return todosExisten;
}

// ====================================================================
// ANIMACIONES DEL LOGO
// ====================================================================
function initializeAnimations() {
    if (loginScreen && loginScreen.classList.contains('active')) {
        runLoginAnimation();
    }
}

function runLoginAnimation() {
    if (typeof anime === 'undefined') {
        console.warn("⚠️ Anime.js no cargado, omitiendo animaciones");
        return;
    }
    
    const timeline = anime.timeline({
        duration: 1200,
        easing: 'easeOutElastic(1, .8)'
    });

    timeline
    .add({
        targets: '#animatedLogo',
        scale: [0, 1.2, 1],
        rotate: '360deg',
        opacity: [0, 1],
        duration: 1500,
    })
    .add({
        targets: '.company-name',
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 800,
    }, '-=500')
    .add({
        targets: '.login-form',
        opacity: [0, 1],
        translateY: [30, 0],
        duration: 600,
    }, '-=300');
}

function animateDashboardLogo() {
    const dashboardLogo = document.getElementById('dashboardLogo');
    if (dashboardLogo && typeof anime !== 'undefined') {
        anime({
            targets: '#dashboardLogo',
            scale: [0.8, 1],
            rotate: '5deg',
            duration: 800,
            easing: 'easeOutBack'
        });
    }
}

// ====================================================================
// FUNCIONES DE TRANSICIÓN MEJORADAS
// ====================================================================
function showDashboardWithAnimation() {
    if (!loginScreen || !dashboardScreen) return;
    
    dashboardScreen.style.opacity = '0';
    dashboardScreen.style.display = 'flex';
    
    if (typeof anime === 'undefined') {
        // Fallback sin animaciones
        loginScreen.style.display = 'none';
        loginScreen.classList.remove('active');
        dashboardScreen.style.display = 'flex';
        dashboardScreen.classList.add('active');
        dashboardScreen.style.opacity = '1';
        return;
    }
    
    const timeline = anime.timeline({
        duration: 800,
        easing: 'easeInOutQuad',
        complete: function() {
            loginScreen.style.display = 'none';
            dashboardScreen.style.opacity = '';
        }
    });

    timeline
    .add({
        targets: loginScreen,
        opacity: [1, 0],
        translateY: [0, -20],
        duration: 400,
        complete: function() {
            loginScreen.classList.remove('active');
        }
    })
    .add({
        targets: dashboardScreen,
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 500,
        begin: function() {
            dashboardScreen.classList.add('active');
        }
    });
}

function showLoginWithAnimation() {
    if (!loginScreen || !dashboardScreen) return;
    
    loginScreen.style.opacity = '0';
    loginScreen.style.display = 'flex';
    
    if (typeof anime === 'undefined') {
        dashboardScreen.style.display = 'none';
        dashboardScreen.classList.remove('active');
        loginScreen.style.display = 'flex';
        loginScreen.classList.add('active');
        loginScreen.style.opacity = '1';
        return;
    }
    
    const timeline = anime.timeline({
        duration: 800,
        easing: 'easeInOutQuad',
        complete: function() {
            dashboardScreen.style.display = 'none';
            loginScreen.style.opacity = '';
        }
    });

    timeline
    .add({
        targets: dashboardScreen,
        opacity: [1, 0],
        translateY: [0, 20],
        duration: 400,
        complete: function() {
            dashboardScreen.classList.remove('active');
        }
    })
    .add({
        targets: loginScreen,
        opacity: [0, 1],
        translateY: [-20, 0],
        duration: 500,
        begin: function() {
            loginScreen.classList.add('active');
        }
    });
}

// ====================================================================
// MANEJO SEGURO DE AUTENTICACIÓN
// ====================================================================
async function secureLogin(username, password) {
    try {
        const loginBtn = loginForm.querySelector('button[type="submit"]');
        const originalText = loginBtn.innerHTML;
        loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> VERIFICANDO...';
        loginBtn.disabled = true;
        
        console.log(`🔐 Intentando login para: ${username}`);
        
        const response = await fetch(`${AUTH_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });

        console.log(`📨 Respuesta login: ${response.status}`);
        const result = await response.json();

        if (response.ok) {
            currentUser = result.user;
            userInitial.textContent = currentUser.name.charAt(0);
            userName.textContent = currentUser.name;

            showDashboardWithAnimation();
            loginError.style.display = "none";

            setTimeout(() => {
                loadInventoryData();
                loadComponentTypes();
                animateDashboardLogo();
            }, 600);
            
            startSessionChecker();
            console.log("✅ Login exitoso");
        } else {
            console.error(`❌ Error login: ${result.error}`);
            showLoginError(result.error || "Credenciales incorrectas");
        }
    } catch (error) {
        console.error("❌ Error de conexión en login:", error);
        showLoginError("Error de conexión con el servidor");
    } finally {
        const loginBtn = loginForm.querySelector('button[type="submit"]');
        if (loginBtn) {
            loginBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> INICIAR SESIÓN';
            loginBtn.disabled = false;
        }
    }
}

async function checkSession() {
    try {
        console.log("🔍 Verificando sesión activa...");
        const response = await fetch(`${AUTH_URL}/check`, {
            credentials: 'include'
        });
        
        console.log(`📨 Respuesta check: ${response.status}`);
        const data = await response.json();
        
        if (response.ok && data.authenticated) {
            currentUser = data.user;
            console.log("✅ Sesión activa encontrada");
            return true;
        } else {
            console.log("❌ No hay sesión activa:", data);
            return false;
        }
    } catch (error) {
        console.error("❌ Error verificando sesión:", error);
        return false;
    }
}

async function secureLogout() {
    try {
        await fetch(`${AUTH_URL}/logout`, {
            method: "POST",
            credentials: 'include'
        });
    } catch (error) {
        console.error("Error en logout:", error);
    } finally {
        currentUser = null;
        ALL_PRODUCT_MODELS = [];
        productTypesCache = null;
        inventoryCache = null;
        selectedSerials.clear();
        
        showLoginWithAnimation();
        
        if (loginForm) loginForm.reset();
        if (loginError) loginError.style.display = "none";
        
        setTimeout(() => {
            runLoginAnimation();
        }, 600);
        
        stopSessionChecker();
        console.log("✅ Logout completado");
    }
}

function startSessionChecker() {
    sessionCheckerInterval = setInterval(async () => {
        const isValid = await checkSession();
        if (!isValid && currentUser) {
            alert("Sesión expirada. Por favor ingresa nuevamente.");
            secureLogout();
        }
    }, 5 * 60 * 1000);
}

function stopSessionChecker() {
    if (sessionCheckerInterval) {
        clearInterval(sessionCheckerInterval);
        sessionCheckerInterval = null;
    }
}

async function secureFetch(url, options = {}) {
    const config = {
        ...options,
        credentials: 'include'
    };
    
    console.log(`📤 Fetch a: ${url}`);
    const response = await fetch(url, config);
    
    if (response.status === 401) {
        console.warn("🔒 Sesión expirada, haciendo logout...");
        secureLogout();
        throw new Error("Sesión expirada");
    }
    
    return response;
}

// ====================================================================
// AUTENTICACIÓN - EVENT LISTENERS
// ====================================================================
if (loginForm) {
    loginForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        
        secureLogin(username, password);
    });
}

if (logoutBtn) {
    logoutBtn.addEventListener("click", secureLogout);
}

function showLoginError(message) {
    if (!loginError) return;
    
    loginError.textContent = message;
    loginError.style.display = "block";
    
    if (typeof anime !== 'undefined') {
        anime({
            targets: '#loginError',
            scale: [0.8, 1],
            duration: 300,
            easing: 'easeOutBack'
        });
    }
}

// ====================================================================
// GESTIÓN DE INVENTARIO
// ====================================================================
async function loadInventoryData(filter = "") {
    try {
        console.log(`📊 Cargando inventario (filtro: "${filter}")`);
        
        if (inventoryTableBody) {
            inventoryTableBody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; padding: 40px;">
                        <div class="loading"></div> Cargando inventario...
                    </td>
                </tr>
            `;
        }

        const [inventoryResponse, statsResponse] = await Promise.all([
            secureFetch(`${INVENTARIO_URL}/stock`),
            secureFetch(`${INVENTARIO_URL}/estadisticas`)
        ]);

        if (!inventoryResponse.ok) {
            throw new Error(`Error HTTP: ${inventoryResponse.status}`);
        }

        let data = await inventoryResponse.json();
        inventoryCache = data;
        renderInventoryTable(data, filter);

        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            updateStatistics(
                stats.total_modelos || data.length,
                stats.modelos_stock_bajo || 0,
                stats.total_seriales || 0
            );
        } else {
            updateStatisticsFromData(data);
        }

    } catch (error) {
        console.error("❌ Error al cargar inventario:", error);
        if (error.message === "Sesión expirada") {
            showLoginError("Sesión expirada");
        } else {
            showInventoryError();
        }
    }
}

function updateStatisticsFromData(data) {
    let totalSeriales = 0;
    let lowStockCount = 0;

    data.forEach(item => {
        totalSeriales += item.stock_disponible;
        if (item.stock_disponible <= 3) lowStockCount++;
    });

    updateStatistics(data.length, lowStockCount, totalSeriales);
}

function renderInventoryTable(data, filter = "") {
    if (!inventoryTableBody) return;
    
    if (filter) {
        const lowerFilter = filter.toLowerCase();
        data = data.filter(item =>
            item.producto.toLowerCase().includes(lowerFilter) || 
            item.codigo_sku.toLowerCase().includes(lowerFilter) ||
            item.tipo_pieza.toLowerCase().includes(lowerFilter)
        );
    }

    inventoryTableBody.innerHTML = "";
    let totalSeriales = 0;
    let lowStockCount = 0;

    if (data.length === 0) {
        inventoryTableBody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px;">
                    <i class="fas fa-search" style="font-size: 24px; margin-bottom: 10px; display: block; color: var(--color-text-secondary);"></i>
                    No se encontraron productos que coincidan con la búsqueda.
                </td>
            </tr>
        `;
        updateStatistics(0, 0, 0);
        return;
    }

    data.forEach((item, index) => {
        const row = document.createElement("tr");
        const stockStatus = item.stock_disponible <= 3 ? "Bajo" : item.stock_disponible === 0 ? "Agotado" : "Normal";
        const statusClass = item.stock_disponible <= 3 ? "danger" : item.stock_disponible === 0 ? "warning" : "success";
        
        const historialDesc = item.ultima_actividad_desc || "Sin actividad reciente";

        totalSeriales += item.stock_disponible;
        if (item.stock_disponible <= 3) lowStockCount++;

        row.innerHTML = `
            <td>${item.producto_id}</td>
            <td><strong>${item.producto}</strong></td>
            <td>${item.tipo_pieza}</td>
            <td><code>${item.codigo_sku}</code></td>
            <td class="stock-cell">
                <button class="btn-stock" data-id="${item.producto_id}" data-name="${item.producto}">
                    <span class="stock-badge">${item.stock_disponible}</span>
                    <i class="fas fa-box-open"></i> Ver Seriales
                </button>
            </td>
            <td><span class="badge badge-${statusClass}">${stockStatus}</span></td>
            <td>
                <span class="historial-text">${historialDesc}</span>
            </td>
            <td>
                <button class="btn-action btn-danger" onclick="eliminarProducto(${item.producto_id}, '${item.producto.replace(/'/g, "\\'")}')" title="Eliminar producto">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;

        inventoryTableBody.appendChild(row);
        
        if (typeof anime !== 'undefined') {
            anime({
                targets: row,
                opacity: [0, 1],
                translateY: [20, 0],
                duration: 400,
                delay: index * 50,
                easing: 'easeOutQuad'
            });
        }
    });

    updateStatistics(data.length, lowStockCount, totalSeriales);
    attachStockButtonEvents();
}

function showInventoryError() {
    if (!inventoryTableBody) return;
    
    inventoryTableBody.innerHTML = `
        <tr>
            <td colspan="8" style="text-align: center; color: var(--color-danger); padding: 40px;">
                <i class="fas fa-exclamation-triangle" style="font-size: 24px; margin-bottom: 10px; display: block;"></i>
                Error al conectar con el servidor. Verifica tu conexión.
            </td>
        </tr>
    `;
}

function attachStockButtonEvents() {
    document.querySelectorAll(".btn-stock").forEach((btn) => {
        btn.addEventListener("click", function () {
            const id = Number.parseInt(this.getAttribute("data-id"));
            const name = this.getAttribute("data-name");
            showSerialsDetail(id, name);
        });
    });
}

// ====================================================================
// GESTIÓN DE SERIALES
// ====================================================================
async function loadComponentTypes() {
    try {
        console.log("📦 Cargando tipos de pieza...");
        
        if (!componentTypeSelect) {
            console.error("❌ componentTypeSelect no encontrado");
            return;
        }

        if (productTypesCache) {
            populateComponentTypes(productTypesCache);
            return;
        }

        const response = await secureFetch(`${INVENTARIO_URL}/tipos_pieza`);
        if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);

        const types = await response.json();
        console.log(`✅ Tipos cargados: ${types.length}`);
        
        if (types.length === 0) {
            await inicializarTiposPredeterminados();
            const newResponse = await secureFetch(`${INVENTARIO_URL}/tipos_pieza`);
            const newTypes = await newResponse.json();
            productTypesCache = newTypes;
            populateComponentTypes(newTypes);
        } else {
            productTypesCache = types;
            populateComponentTypes(types);
        }
        
        await fetchAllProductModels();

    } catch (error) {
        console.error("❌ Error al cargar tipos de pieza:", error);
        if (componentTypeSelect) {
            componentTypeSelect.innerHTML = '<option value="">Error al cargar categorías</option>';
        }
    }
}

async function inicializarTiposPredeterminados() {
    try {
        console.log("📦 Inicializando tipos predeterminados...");
        const response = await secureFetch(`${INVENTARIO_URL}/inicializar_tipos`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log("✅ Tipos predeterminados inicializados:", result.mensaje);
        }
    } catch (error) {
        console.error("Error inicializando tipos predeterminados:", error);
    }
}

function populateComponentTypes(types) {
    if (!componentTypeSelect) return;
    
    componentTypeSelect.innerHTML = '<option value="">-- Selecciona una categoría --</option>';
    types.forEach((t) => {
        const option = document.createElement("option");
        option.value = t.tipo_id;
        option.textContent = t.tipo_modelo;
        componentTypeSelect.appendChild(option);
    });
}

async function fetchAllProductModels() {
    try {
        console.log("📦 Cargando todos los modelos...");
        const response = await secureFetch(`${INVENTARIO_URL}/productos`);
        if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
        
        ALL_PRODUCT_MODELS = await response.json();
        console.log(`✅ Modelos cargados: ${ALL_PRODUCT_MODELS.length}`);
    } catch (error) {
        console.error("❌ Error al cargar todos los modelos:", error);
        if (serialProductSelect) {
            serialProductSelect.innerHTML = '<option value="">Error al cargar modelos</option>';
        }
    }
}

function filterProductModels() {
    if (!serialProductSelect) return;
    
    const selectedTypeId = parseInt(componentTypeSelect.value);
    
    if (!selectedTypeId) {
        serialProductSelect.innerHTML = '<option value="">-- Selecciona un modelo (elige categoría primero) --</option>';
        serialProductSelect.disabled = true;
        return;
    }

    serialProductSelect.innerHTML = '<option value="">-- Selecciona un modelo específico --</option>';
    const filteredModels = ALL_PRODUCT_MODELS.filter(model => model.tipo_pieza_id === selectedTypeId);

    if (filteredModels.length === 0) {
        serialProductSelect.innerHTML = '<option value="">-- No hay modelos para esta categoría --</option>';
    } else {
        filteredModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model.producto_id;
            option.textContent = `${model.nombre} (SKU: ${model.codigo_sku})`;
            serialProductSelect.appendChild(option);
        });
    }

    serialProductSelect.disabled = false;
}

async function showSerialsDetail(productoId, productoNombre) {
    currentProductId = productoId;
    
    if (serialsModalTitle) {
        serialsModalTitle.innerHTML = `<i class="fas fa-boxes"></i> Gestión de Seriales: ${productoNombre}`;
    }
    
    if (serialsTableBody) {
        serialsTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px;"><div class="loading"></div> Cargando seriales...</td></tr>';
    }
    
    if (serialsDetailModal) {
        serialsDetailModal.style.display = "flex";
    }
    
    selectedSerials.clear();
    updateActionButtons();

    if (typeof anime !== 'undefined') {
        anime({
            targets: serialsDetailModal,
            opacity: [0, 1],
            scale: [0.9, 1],
            duration: 400,
            easing: 'easeOutBack'
        });
    }

    try {
        const response = await secureFetch(`${INVENTARIO_URL}/seriales/${productoId}`);
        if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);

        const serials = await response.json();
        renderSerialsTable(serials, productoNombre);

    } catch (error) {
        console.error("❌ Error al cargar seriales:", error);
        if (serialsTableBody) {
            serialsTableBody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; color: var(--color-danger); padding: 20px;">
                        <i class="fas fa-exclamation-triangle"></i> Error al obtener seriales
                    </td>
                </tr>
            `;
        }
    }
}

function renderSerialsTable(serials, productoNombre) {
    if (!serialsTableBody) return;
    
    serialsTableBody.innerHTML = "";

    if (serials.length === 0) {
        serialsTableBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: var(--color-text-secondary);">
                    <i class="fas fa-inbox" style="font-size: 32px; margin-bottom: 10px; display: block;"></i>
                    No hay seriales registrados para <strong>${productoNombre}</strong>
                </td>
            </tr>
        `;
        return;
    }

    const contadores = {
        ALMACEN: 0,
        INSTALADO: 0,
        DAÑADO: 0,
        RETIRADO: 0
    };

    serials.forEach((s, index) => {
        contadores[s.estado]++;
        
        const row = document.createElement("tr");
        row.className = `serial-row ${s.estado.toLowerCase()}`;
        
        const statusClass = s.estado === 'ALMACEN' ? 'success' : 
                           s.estado === 'INSTALADO' ? 'primary' : 
                           s.estado === 'DAÑADO' ? 'danger' : 'warning';

        row.innerHTML = `
            <td>${s.serial_id}</td>
            <td><code>${s.codigo_unico_serial}</code></td>
            <td>
                <span class="badge badge-${statusClass}">
                    ${s.estado === 'ALMACEN' ? '🟢' : s.estado === 'INSTALADO' ? '🔵' : s.estado === 'DAÑADO' ? '🔴' : '🟡'} ${s.estado}
                </span>
            </td>
            <td>${s.fecha_ingreso || 'N/A'}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn-action change-status" data-serial-id="${s.serial_id}" data-current-status="${s.estado}" title="Cambiar estado">
                        <i class="fas fa-exchange-alt"></i>
                    </button>
                    ${currentUser?.role === 'admin' ? `
                    <button class="btn-action delete-serial" data-serial-id="${s.serial_id}" data-serial-code="${s.codigo_unico_serial}" title="Eliminar serial">
                        <i class="fas fa-trash"></i>
                    </button>
                    ` : ''}
                </div>
            </td>
        `;

        serialsTableBody.appendChild(row);
        
        if (typeof anime !== 'undefined') {
            anime({
                targets: row,
                opacity: [0, 1],
                translateX: [-20, 0],
                duration: 300,
                delay: index * 80,
                easing: 'easeOutQuad'
            });
        }
    });

    if (serialsModalTitle) {
        serialsModalTitle.innerHTML = `
            <i class="fas fa-boxes"></i> ${productoNombre}
            <small style="display: block; font-size: 14px; color: var(--color-text-secondary); margin-top: 5px;">
                🟢 ${contadores.ALMACEN} Almacén | 🔵 ${contadores.INSTALADO} Instalado | 🔴 ${contadores.DAÑADO} Dañado | 🟡 ${contadores.RETIRADO} Retirado
            </small>
        `;
    }

    attachSerialActionEvents();
}

function attachSerialActionEvents() {
    document.querySelectorAll(".change-status").forEach((btn) => {
        btn.addEventListener("click", function () {
            const serialId = this.getAttribute("data-serial-id");
            const currentStatus = this.getAttribute("data-current-status");
            showChangeStatusModal(serialId, currentStatus);
        });
    });

    if (currentUser?.role === 'admin') {
        document.querySelectorAll(".delete-serial").forEach((btn) => {
            btn.addEventListener("click", function () {
                const serialId = this.getAttribute("data-serial-id");
                const serialCode = this.getAttribute("data-serial-code");
                confirmDeleteSerial(serialId, serialCode);
            });
        });
    }
}

function showChangeStatusModal(serialId, currentStatus) {
    currentSerialId = serialId;
    
    if (newStatusSelect) newStatusSelect.value = "";
    if (statusNotes) statusNotes.value = "";
    if (statusMessage) statusMessage.style.display = "none";
    
    if (changeStatusModal) {
        changeStatusModal.style.display = "flex";
    }
    
    if (typeof anime !== 'undefined') {
        anime({
            targets: changeStatusModal,
            opacity: [0, 1],
            scale: [0.8, 1],
            duration: 400,
            easing: 'easeOutBack'
        });
    }
}

if (confirmStatusChange) {
    confirmStatusChange.addEventListener("click", async () => {
        if (!newStatusSelect || !statusMessage) return;
        
        const nuevoEstado = newStatusSelect.value;
        const notas = statusNotes ? statusNotes.value.trim() : "";

        if (!nuevoEstado) {
            showMessage(statusMessage, "❌ Por favor selecciona un estado", "danger");
            return;
        }

        try {
            const response = await secureFetch(`${INVENTARIO_URL}/serial/${currentSerialId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    estado: nuevoEstado,
                    notas: notas
                })
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(statusMessage, `✅ ${result.mensaje}`, "success");
                
                if (typeof anime !== 'undefined') {
                    anime({
                        targets: statusMessage,
                        scale: [0.8, 1],
                        duration: 300,
                        easing: 'easeOutBack'
                    });
                }
                
                setTimeout(() => {
                    if (changeStatusModal) changeStatusModal.style.display = "none";
                    if (serialsModalTitle) {
                        showSerialsDetail(currentProductId, serialsModalTitle.textContent.split(': ')[1]);
                    }
                }, 1500);
            } else {
                showMessage(statusMessage, `❌ ${result.error}`, "danger");
            }
        } catch (error) {
            console.error("Error al cambiar estado:", error);
            showMessage(statusMessage, "❌ Error de conexión con el servidor", "danger");
        }
    });
}

if (cancelStatusChange) {
    cancelStatusChange.addEventListener("click", () => {
        if (!changeStatusModal) return;
        
        if (typeof anime !== 'undefined') {
            anime({
                targets: changeStatusModal,
                opacity: [1, 0],
                scale: [1, 0.8],
                duration: 300,
                easing: 'easeInQuad',
                complete: function() {
                    changeStatusModal.style.display = "none";
                }
            });
        } else {
            changeStatusModal.style.display = "none";
        }
    });
}

function confirmDeleteSerial(serialId, serialCode) {
    if (confirm(`¿Estás seguro de que quieres eliminar permanentemente el serial:\n\n"${serialCode}"?\n\nEsta acción no se puede deshacer.`)) {
        deleteSerial(serialId);
    }
}

async function deleteSerial(serialId) {
    try {
        const response = await secureFetch(`${INVENTARIO_URL}/serial/${serialId}`, {
            method: "DELETE"
        });

        const result = await response.json();

        if (response.ok) {
            alert(`✅ ${result.mensaje}`);
            if (serialsModalTitle) {
                showSerialsDetail(currentProductId, serialsModalTitle.textContent.split(': ')[1]);
            }
        } else {
            alert(`❌ ${result.error}`);
        }
    } catch (error) {
        console.error("Error al eliminar serial:", error);
        alert("❌ Error de conexión con el servidor");
    }
}

function updateActionButtons() {
    if (!btnMarcarInstalados || !btnMarcarDanados || !btnMarcarRetirados) return;
    
    const hasSelection = selectedSerials.size > 0;
    btnMarcarInstalados.style.display = hasSelection ? 'inline-block' : 'none';
    btnMarcarDanados.style.display = hasSelection ? 'inline-block' : 'none';
    btnMarcarRetirados.style.display = hasSelection ? 'inline-block' : 'none';
}

// ====================================================================
// REGISTRO DE SERIALES
// ====================================================================
if (serialForm) {
    serialForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (serialMessage) serialMessage.style.display = "none";

        if (!componentTypeSelect || !serialProductSelect) {
            showMessage(serialMessage, "❌ Error en formulario", "danger");
            return;
        }

        if (!componentTypeSelect.value || !serialProductSelect.value) {
            showMessage(serialMessage, "❌ Por favor selecciona tanto la categoría como el modelo", "danger");
            return;
        }

        const newSerial = {
            producto_id: Number.parseInt(serialProductSelect.value),
            codigo_unico_serial: serialCode ? serialCode.value.trim() : "",
        };

        if (!newSerial.codigo_unico_serial) {
            showMessage(serialMessage, "❌ Por favor ingresa un código de serial", "danger");
            return;
        }

        try {
            const response = await secureFetch(`${INVENTARIO_URL}/serial`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(newSerial),
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(serialMessage, `✅ ${result.mensaje}`, "success");
                serialForm.reset();
                inventoryCache = null;
                loadInventoryData();
                
                if (typeof anime !== 'undefined') {
                    anime({
                        targets: serialMessage,
                        scale: [0.8, 1],
                        duration: 300,
                        easing: 'easeOutBack'
                    });
                }
                
                setTimeout(() => {
                    if (itemModal) itemModal.style.display = "none";
                    if (serialMessage) serialMessage.style.display = "none";
                }, 2000);
            } else {
                showMessage(serialMessage, `❌ ${result.error}`, "danger");
            }
        } catch (error) {
            console.error("Error al registrar serial:", error);
            showMessage(serialMessage, "❌ Error de conexión con el servidor", "danger");
        }
    });
}

// ====================================================================
// GESTIÓN DE PRODUCTOS
// ====================================================================
if (addProductBtn) {
    addProductBtn.addEventListener("click", () => {
        console.log("🆕 Abriendo modal de producto...");
        if (productModal) {
            productModal.style.display = "flex";
        }
        if (productForm) productForm.reset();
        if (productMessage) productMessage.style.display = "none";
        loadProductTypes();
        
        if (typeof anime !== 'undefined') {
            anime({
                targets: productModal,
                opacity: [0, 1],
                scale: [0.9, 1],
                duration: 400,
                easing: 'easeOutBack'
            });
        }
    });
}

async function loadProductTypes() {
    try {
        console.log("📦 Cargando categorías para producto...");
        
        if (!productTypeSelect) {
            console.error("❌ productTypeSelect no encontrado");
            return;
        }

        productTypeSelect.innerHTML = '<option value="">Cargando categorías...</option>';
        
        if (productTypesCache) {
            console.log("📦 Usando caché de categorías:", productTypesCache.length);
            populateProductTypes(productTypesCache);
            return;
        }

        const response = await secureFetch(`${INVENTARIO_URL}/tipos_pieza`);
        if (!response.ok) throw new Error('Error al cargar categorías');
        
        const types = await response.json();
        console.log(`✅ Categorías cargadas: ${types.length} tipos`);
        
        if (types.length === 0) {
            console.log("📦 No hay categorías, inicializando predeterminadas...");
            await inicializarTiposPredeterminados();
            const newResponse = await secureFetch(`${INVENTARIO_URL}/tipos_pieza`);
            const newTypes = await newResponse.json();
            productTypesCache = newTypes;
            populateProductTypes(newTypes);
        } else {
            productTypesCache = types;
            populateProductTypes(types);
        }
        
    } catch (error) {
        console.error("❌ Error al cargar categorías:", error);
        if (productTypeSelect) {
            productTypeSelect.innerHTML = `
                <option value="">Error cargando categorías</option>
                <option value="reload" onclick="location.reload()">↻ Recargar página</option>
            `;
        }
    }
}

function populateProductTypes(types) {
    if (!productTypeSelect) return;
    
    productTypeSelect.innerHTML = '<option value="">-- Selecciona una categoría --</option>';
    types.forEach((t) => {
        const option = document.createElement("option");
        option.value = t.tipo_id;
        option.textContent = t.tipo_modelo;
        productTypeSelect.appendChild(option);
    });
    
    console.log(`✅ Select poblado con ${types.length} categorías`);
}

function sugerirSKU(nombre) {
    if (!nombre) return '';
    
    const palabras = nombre.split(' ').filter(palabra => palabra.length > 0);
    let skuSugerido = '';
    
    for (let i = 0; i < Math.min(palabras.length, 3); i++) {
        skuSugerido += palabras[i].substring(0, 3).toUpperCase();
        if (i < Math.min(palabras.length, 3) - 1) {
            skuSugerido += '-';
        }
    }
    
    return skuSugerido;
}

if (productForm) {
    productForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (productMessage) productMessage.style.display = "none";

        if (!productNameInput || !productTypeSelect || !productSKUInput) {
            showMessage(productMessage, "❌ Error en formulario", "danger");
            return;
        }

        const newProduct = {
            nombre: productNameInput.value.trim(),
            descripcion: productDescription ? productDescription.value.trim() : "",
            tipo_pieza_id: parseInt(productTypeSelect.value),
            codigo_sku: productSKUInput.value.trim()
        };

        if (!newProduct.nombre || !newProduct.tipo_pieza_id || !newProduct.codigo_sku) {
            showMessage(productMessage, "❌ Por favor completa todos los campos requeridos", "danger");
            return;
        }

        try {
            const response = await secureFetch(`${INVENTARIO_URL}/productos`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(newProduct),
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(productMessage, `✅ ${result.mensaje}`, "success");
                productForm.reset();
                
                ALL_PRODUCT_MODELS = [];
                productTypesCache = null;
                inventoryCache = null;
                
                await fetchAllProductModels();
                loadInventoryData();
                loadComponentTypes();
                
                if (typeof anime !== 'undefined') {
                    anime({
                        targets: productMessage,
                        scale: [0.8, 1],
                        duration: 300,
                        easing: 'easeOutBack'
                    });
                }
                
                setTimeout(() => {
                    if (productModal) productModal.style.display = "none";
                    if (productMessage) productMessage.style.display = "none";
                }, 2000);
            } else {
                showMessage(productMessage, `❌ ${result.error}`, "danger");
            }
        } catch (error) {
            console.error("Error al registrar producto:", error);
            showMessage(productMessage, "❌ Error de conexión con el servidor", "danger");
        }
    });
}

// ====================================================================
// ELIMINAR PRODUCTO
// ====================================================================
async function eliminarProducto(productoId, productoNombre) {
    if (!confirm(`¿Eliminar el producto "${productoNombre}"?\n\nEsta acción no se puede deshacer.`)) {
        return;
    }

    try {
        const response = await secureFetch(`${INVENTARIO_URL}/productos/${productoId}`, {
            method: "DELETE"
        });

        const result = await response.json();

        if (response.ok) {
            alert(`✅ ${result.mensaje}`);
            loadInventoryData();
        } else {
            alert(`❌ ${result.error}`);
        }
    } catch (error) {
        console.error("Error eliminando producto:", error);
        alert("❌ Error de conexión");
    }
}

// ====================================================================
// FUNCIONES AUXILIARES
// ====================================================================
function updateStatistics(totalModelos, lowStockCount, totalSeriales) {
    animateCounter(totalItems, totalModelos);
    animateCounter(lowStockItems, lowStockCount);
    animateCounter(totalValue, totalSeriales);
}

function animateCounter(element, targetValue) {
    if (!element || typeof anime === 'undefined') {
        if (element) element.textContent = targetValue;
        return;
    }
    
    const currentValue = parseInt(element.textContent) || 0;
    anime({
        targets: { value: currentValue },
        value: targetValue,
        duration: 800,
        easing: 'easeOutQuad',
        update: function(anim) {
            element.textContent = Math.floor(anim.animations[0].currentValue);
        }
    });
}

function showMessage(element, message, type) {
    if (!element) return;
    
    element.textContent = message;
    element.className = `alert alert-${type}`;
    element.style.display = "block";
}

// ====================================================================
// EVENTOS DE MODALES Y BÚSQUEDA
// ====================================================================
if (addItemBtn) {
    addItemBtn.addEventListener("click", () => {
        console.log("➕ Abriendo modal para registrar serial...");
        if (itemModal) {
            itemModal.style.display = "flex";
        }
        if (serialForm) serialForm.reset();
        if (serialMessage) serialMessage.style.display = "none";
        if (componentTypeSelect) {
            componentTypeSelect.innerHTML = '<option value="">-- Selecciona una categoría --</option>';
        }
        if (serialProductSelect) {
            serialProductSelect.innerHTML = '<option value="">-- Selecciona un modelo (elige categoría primero) --</option>';
            serialProductSelect.disabled = true;
        }
        loadComponentTypes();
        
        if (typeof anime !== 'undefined') {
            anime({
                targets: itemModal,
                opacity: [0, 1],
                scale: [0.9, 1],
                duration: 400,
                easing: 'easeOutBack'
            });
        }
    });
}

if (productNameInput && productSKUInput) {
    productNameInput.addEventListener("input", function() {
        if (!productSKUInput.value) {
            const skuSugerido = sugerirSKU(this.value);
            productSKUInput.placeholder = `Ej: ${skuSugerido || 'SKU-PRODUCTO'}`;
        }
    });
}

if (componentTypeSelect) {
    componentTypeSelect.addEventListener('change', filterProductModels);
}

function closeModalWithAnimation(modal) {
    if (!modal) return;
    
    if (typeof anime !== 'undefined') {
        anime({
            targets: modal,
            opacity: [1, 0],
            scale: [1, 0.9],
            duration: 300,
            easing: 'easeInQuad',
            complete: function() {
                modal.style.display = "none";
            }
        });
    } else {
        modal.style.display = "none";
    }
}

if (closeModal) {
    closeModal.addEventListener("click", () => {
        closeModalWithAnimation(itemModal);
    });
}

if (closeProductModal) {
    closeProductModal.addEventListener("click", () => {
        closeModalWithAnimation(productModal);
    });
}

// Event listeners para modal de crear categoría
if (addNewCategoryBtn) {
    addNewCategoryBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log("🆕 Botón Nueva Categoría clickeado (1)");
        if (categoryModal) {
            categoryModal.style.display = "flex";
        }
        if (categoryForm) categoryForm.reset();
        if (categoryMessage) categoryMessage.style.display = "none";
        
        if (typeof anime !== 'undefined') {
            anime({
                targets: categoryModal,
                opacity: [0, 1],
                scale: [0.9, 1],
                duration: 400,
                easing: 'easeOutBack'
            });
        }
    });
}

if (newCategoryBtn) {
    newCategoryBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log("🆕 Botón Nueva Categoría clickeado (2)");
        if (categoryModal) {
            categoryModal.style.display = "flex";
        }
        if (categoryForm) categoryForm.reset();
        if (categoryMessage) categoryMessage.style.display = "none";
        
        if (typeof anime !== 'undefined') {
            anime({
                targets: categoryModal,
                opacity: [0, 1],
                scale: [0.9, 1],
                duration: 400,
                easing: 'easeOutBack'
            });
        }
    });
}

if (closeCategoryModal) {
    closeCategoryModal.addEventListener("click", () => {
        closeModalWithAnimation(categoryModal);
    });
}

if (closeSerialsModal) {
    closeSerialsModal.addEventListener("click", () => {
        closeModalWithAnimation(serialsDetailModal);
    });
}

if (closeStatusModal) {
    closeStatusModal.addEventListener("click", () => {
        closeModalWithAnimation(changeStatusModal);
    });
}

// Cerrar modal al hacer click fuera
window.addEventListener("click", (e) => {
    if (itemModal && e.target == itemModal) closeModalWithAnimation(itemModal);
    if (productModal && e.target == productModal) closeModalWithAnimation(productModal);
    if (serialsDetailModal && e.target == serialsDetailModal) closeModalWithAnimation(serialsDetailModal);
    if (changeStatusModal && e.target == changeStatusModal) closeModalWithAnimation(changeStatusModal);
    if (categoryModal && e.target == categoryModal) closeModalWithAnimation(categoryModal);
});

if (searchBtn) {
    searchBtn.addEventListener("click", () => {
        loadInventoryData(searchInput ? searchInput.value : "");
    });
}

if (searchInput) {
    searchInput.addEventListener("keyup", (e) => {
        if (e.key === "Enter") {
            loadInventoryData(searchInput.value);
        }
    });

    searchInput.addEventListener("input", (e) => {
        if (e.target.value === "") {
            loadInventoryData("");
        }
    });
}

// Registrar nueva categoría
if (categoryForm) {
    categoryForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (categoryMessage) categoryMessage.style.display = "none";

        const categoryName = categoryNameInput ? categoryNameInput.value.trim() : "";

        if (!categoryName) {
            showMessage(categoryMessage, "❌ Por favor ingresa el nombre de la categoría", "danger");
            return;
        }

        try {
            const response = await secureFetch(`${INVENTARIO_URL}/tipos_pieza`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tipo_modelo: categoryName }),
            });

            const result = await response.json();

            if (response.ok) {
                showMessage(categoryMessage, `✅ ${result.mensaje}`, "success");
                if (categoryForm) categoryForm.reset();
                
                productTypesCache = null;
                loadProductTypes();
                loadComponentTypes();
                
                setTimeout(() => {
                    if (categoryModal) categoryModal.style.display = "none";
                }, 1500);
            } else {
                showMessage(categoryMessage, `❌ ${result.error}`, "danger");
            }
        } catch (error) {
            console.error("Error:", error);
            showMessage(categoryMessage, "❌ Error al crear la categoría", "danger");
        }
    });
}

// ====================================================================
// INICIALIZACIÓN SEGURA
// ====================================================================
document.addEventListener("DOMContentLoaded", async () => {
    console.log("🚀 DOM completamente cargado");
    
    // Verificar elementos críticos
    const domOk = verificarElementosDOM();
    if (!domOk) {
        console.error("❌ Elementos DOM críticos faltantes");
        alert("Error crítico: Algunos elementos necesarios no se encontraron. Recarga la página.");
        return;
    }
    
    // Asegurar que solo el login esté visible inicialmente
    if (loginScreen) {
        loginScreen.classList.add('active');
        loginScreen.style.display = 'flex';
    }
    
    if (dashboardScreen) {
        dashboardScreen.classList.remove('active');
        dashboardScreen.style.display = 'none';
    }
    
    // Inicializar animaciones
    initializeAnimations();
    
    // Verificar sesión existente
    console.log("🔍 Verificando sesión existente...");
    try {
        const hasSession = await checkSession();
        
        if (hasSession && currentUser) {
            console.log("✅ Sesión encontrada, cargando dashboard...");
            // Mostrar dashboard directamente
            if (loginScreen) {
                loginScreen.classList.remove('active');
                loginScreen.style.display = 'none';
            }
            if (dashboardScreen) {
                dashboardScreen.classList.add('active');
                dashboardScreen.style.display = 'flex';
            }
            
            // Cargar datos del dashboard
            userInitial.textContent = currentUser.name.charAt(0);
            userName.textContent = currentUser.name;
            
            loadInventoryData();
            loadComponentTypes();
            animateDashboardLogo();
            startSessionChecker();
        } else {
            console.log("❌ No hay sesión activa, mostrando login");
            // Asegurar que solo el login esté visible
            if (loginScreen) {
                loginScreen.classList.add('active');
                loginScreen.style.display = 'flex';
            }
            if (dashboardScreen) {
                dashboardScreen.classList.remove('active');
                dashboardScreen.style.display = 'none';
            }
        }
    } catch (error) {
        console.error("❌ Error verificando sesión:", error);
        // Por seguridad, mostrar login
        if (loginScreen) {
            loginScreen.style.display = 'flex';
            loginScreen.classList.add('active');
        }
    }
    
    console.log("✅ Sistema de inventario para Soluciones Lógicas inicializado correctamente");
});

// Agregar estilos CSS dinámicos para mejor visualización
const dynamicStyles = `
<style>
.stock-badge {
    background: var(--color-primary);
    color: white;
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: bold;
    margin-right: 8px;
}

.btn-stock {
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.3s ease;
}

.btn-stock:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.serial-row.almacen { background: rgba(0, 255, 136, 0.05); }
.serial-row.instalado { background: rgba(0, 102, 255, 0.05); }
.serial-row.dañado { background: rgba(255, 68, 68, 0.05); }
.serial-row.retirado { background: rgba(255, 170, 0, 0.05); }

.action-buttons {
    display: flex;
    gap: 5px;
}

.btn-action {
    padding: 6px 10px;
    border: none;
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    font-size: 12px;
    transition: var(--transition);
}

.btn-action.change-status {
    background: var(--color-primary);
    color: white;
}

.btn-action.delete-serial {
    background: var(--color-danger);
    color: white;
}

.btn-action:hover {
    transform: scale(1.1);
    opacity: 0.9;
}

.historial-text {
    color: var(--color-text-secondary);
    font-size: 13px;
}

.modal {
    transition: opacity 0.3s ease;
}

.loading {
    border: 3px solid #f3f3f3;
    border-top: 3px solid var(--color-primary);
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
    margin: 0 auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.login-btn {
    width: 100%;
    padding: 18px 30px;
    background: var(--color-gradient);
    color: white;
    border: none;
    border-radius: var(--border-radius);
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    transition: var(--transition);
    text-transform: uppercase;
    letter-spacing: 1px;
    position: relative;
    overflow: hidden;
    margin-top: 10px;
}

.login-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.6s;
}

.login-btn:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-medium);
    background: var(--color-gradient-hover);
}

.login-btn:hover::before {
    left: 100%;
}

.login-btn:active {
    transform: translateY(-1px);
}

.login-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    transform: none;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', dynamicStyles);

// Exportar funciones globales para acceso desde HTML
window.eliminarProducto = eliminarProducto;