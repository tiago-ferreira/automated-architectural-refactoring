const express = require('express');
const { settings } = require('./config/settings');
const DatabaseClient = require('./config/database');
const CourseModel = require('./models/courseModel');
const UserModel = require('./models/userModel');
const EnrollmentModel = require('./models/enrollmentModel');
const ReportModel = require('./models/reportModel');
const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');
const createRoutes = require('./views/routes');
const errorHandler = require('./middlewares/errorHandler');

async function createApp() {
    const app = express();
    app.use(express.json());

    const db = new DatabaseClient();
    await db.initSchemaAndSeed();

    const courseModel = new CourseModel(db);
    const userModel = new UserModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const reportModel = new ReportModel(db);

    const checkoutController = new CheckoutController({
        courseModel,
        userModel,
        enrollmentModel
    });
    const reportController = new ReportController({ reportModel });
    const userController = new UserController({ userModel });

    app.use(createRoutes({ checkoutController, reportController, userController }));
    app.use(errorHandler);

    return app;
}

if (require.main === module) {
    createApp()
        .then((app) => {
            app.listen(settings.port, () => {
                console.log(`LMS API (MVC) rodando na porta ${settings.port}...`);
            });
        })
        .catch((err) => {
            console.error('Falha ao inicializar a aplicação:', err);
            process.exit(1);
        });
}

module.exports = { createApp };
