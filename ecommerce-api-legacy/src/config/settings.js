const crypto = require('crypto');

const DEFAULT_PORT = 3000;
const SALT_BYTES = 16;
const KEY_LENGTH_BYTES = 32;
const MAX_CACHE_ENTRIES = 100;
const APPROVED_CARD_PREFIX = '4';

const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED'
});

const settings = Object.freeze({
    port: Number(process.env.PORT) || DEFAULT_PORT,
    dbPath: process.env.DB_PATH || ':memory:',
    dbUser: process.env.DB_USER || 'admin_master',
    dbPass: process.env.DB_PASS || '',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'configured_via_env',
    smtpUser: process.env.SMTP_USER || 'no-reply@fullcycle.com.br',
    approvedCardPrefix: APPROVED_CARD_PREFIX,
    paymentStatus: PAYMENT_STATUS
});

class BoundedAuditCache {
    constructor(maxEntries = MAX_CACHE_ENTRIES) {
        this.maxEntries = maxEntries;
        this.store = new Map();
    }

    set(key, value) {
        if (this.store.size >= this.maxEntries && !this.store.has(key)) {
            const oldestKey = this.store.keys().next().value;
            this.store.delete(oldestKey);
        }
        this.store.set(key, value);
    }

    get(key) {
        return this.store.get(key);
    }
}

const auditCache = new BoundedAuditCache();

function hashPassword(password) {
    const rawPassword = String(password || '');
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const derivedKey = crypto.scryptSync(rawPassword, salt, KEY_LENGTH_BYTES).toString('hex');
    return `${salt}:${derivedKey}`;
}

function maskCardNumber(cardNumber) {
    const digits = String(cardNumber || '');
    const lastFour = digits.slice(-4).padStart(4, '*');
    return `****-****-****-${lastFour}`;
}

module.exports = {
    settings,
    auditCache,
    hashPassword,
    maskCardNumber,
    PAYMENT_STATUS
};
