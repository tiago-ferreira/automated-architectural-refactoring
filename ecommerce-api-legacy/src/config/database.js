const sqlite3 = require('sqlite3').verbose();
const { settings, hashPassword, PAYMENT_STATUS } = require('./settings');

class DatabaseClient {
    constructor(dbPath = settings.dbPath) {
        this.rawDb = new sqlite3.Database(dbPath);
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.rawDb.run(sql, params, function onRun(err) {
                if (err) {
                    return reject(err);
                }
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.rawDb.get(sql, params, (err, row) => {
                if (err) {
                    return reject(err);
                }
                resolve(row || null);
            });
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.rawDb.all(sql, params, (err, rows) => {
                if (err) {
                    return reject(err);
                }
                resolve(rows || []);
            });
        });
    }

    async withTransaction(workFn) {
        await this.run('BEGIN TRANSACTION');
        try {
            const result = await workFn();
            await this.run('COMMIT');
            return result;
        } catch (err) {
            await this.run('ROLLBACK');
            throw err;
        }
    }

    async initSchemaAndSeed() {
        await this.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
        await this.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
        await this.run('CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
        await this.run('CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
        await this.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

        const existingCourses = await this.get('SELECT COUNT(*) AS count FROM courses');
        if (!existingCourses || existingCourses.count === 0) {
            const initialPassHash = hashPassword(process.env.INITIAL_ADMIN_PASS || 'initial_seed_secret');
            await this.run(
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                ['Leonan', 'leonan@fullcycle.com.br', initialPassHash]
            );
            await this.run(
                'INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)',
                ['Clean Architecture', 997.00, 1, 'Docker', 497.00, 1]
            );
            await this.run(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                [1, 1]
            );
            await this.run(
                'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [1, 997.00, PAYMENT_STATUS.PAID]
            );
        }
    }
}

module.exports = DatabaseClient;
