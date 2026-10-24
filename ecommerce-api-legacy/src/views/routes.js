const express = require('express');

function createRoutes({ checkoutController, reportController, userController }) {
    const router = express.Router();

    router.post('/api/checkout', (req, res, next) =>
        checkoutController.checkout(req, res, next)
    );
    router.get('/api/admin/financial-report', (req, res, next) =>
        reportController.getFinancialReport(req, res, next)
    );
    router.delete('/api/users/:id', (req, res, next) =>
        userController.deleteUser(req, res, next)
    );

    return router;
}

module.exports = createRoutes;
