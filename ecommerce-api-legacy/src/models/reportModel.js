const { PAYMENT_STATUS } = require('../config/settings');

class ReportModel {
    constructor(db) {
        this.db = db;
    }

    async getFinancialReport() {
        const rows = await this.db.all(`
            SELECT
                c.id AS course_id,
                c.title AS course_title,
                e.id AS enrollment_id,
                u.name AS student_name,
                p.amount AS payment_amount,
                p.status AS payment_status
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            LEFT JOIN users u ON u.id = e.user_id
            LEFT JOIN payments p ON p.enrollment_id = e.id
            ORDER BY c.id, e.id
        `);

        const coursesMap = new Map();

        for (const row of rows) {
            if (!coursesMap.has(row.course_id)) {
                coursesMap.set(row.course_id, {
                    course: row.course_title,
                    revenue: 0,
                    students: []
                });
            }

            const courseEntry = coursesMap.get(row.course_id);
            if (row.enrollment_id !== null && row.enrollment_id !== undefined) {
                const paidAmount = row.payment_amount ? Number(row.payment_amount) : 0;
                if (row.payment_status === PAYMENT_STATUS.PAID) {
                    courseEntry.revenue += paidAmount;
                }
                courseEntry.students.push({
                    student: row.student_name || 'Unknown',
                    paid: paidAmount
                });
            }
        }

        return Array.from(coursesMap.values());
    }
}

module.exports = ReportModel;
