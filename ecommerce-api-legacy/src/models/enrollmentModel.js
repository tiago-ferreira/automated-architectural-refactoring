class EnrollmentModel {
    constructor(db) {
        this.db = db;
    }

    async createEnrollmentWithPaymentAndAudit({ userId, courseId, amount, status }) {
        return this.db.withTransaction(async () => {
            const enrollmentResult = await this.db.run(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                [userId, courseId]
            );
            const enrollmentId = enrollmentResult.lastID;

            await this.db.run(
                'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [enrollmentId, amount, status]
            );

            await this.db.run(
                "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                [`Checkout curso ${courseId} por ${userId}`]
            );

            return enrollmentId;
        });
    }
}

module.exports = EnrollmentModel;
