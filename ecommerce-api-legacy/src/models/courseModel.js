class CourseModel {
    constructor(db) {
        this.db = db;
    }

    async findActiveById(courseId) {
        return this.db.get(
            'SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1',
            [courseId]
        );
    }

    async findAll() {
        return this.db.all('SELECT id, title, price, active FROM courses ORDER BY id');
    }
}

module.exports = CourseModel;
