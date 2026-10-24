const { settings, auditCache, maskCardNumber, PAYMENT_STATUS } = require('../config/settings');

class CheckoutController {
    constructor({ courseModel, userModel, enrollmentModel }) {
        this.courseModel = courseModel;
        this.userModel = userModel;
        this.enrollmentModel = enrollmentModel;
    }

    async checkout(req, res, next) {
        try {
            const {
                usr: userName,
                eml: email,
                pwd: password,
                c_id: courseId,
                card: cardNumber
            } = req.body || {};

            if (!userName || !email || !courseId || !cardNumber) {
                return res.status(400).send('Bad Request');
            }

            const course = await this.courseModel.findActiveById(courseId);
            if (!course) {
                return res.status(404).send('Curso não encontrado');
            }

            let user = await this.userModel.findByEmail(email);
            let userId = user ? user.id : null;

            if (!userId) {
                userId = await this.userModel.create({
                    name: userName,
                    email,
                    password: password || ''
                });
            }

            const maskedCard = maskCardNumber(cardNumber);
            console.info(`[INFO] Processando pagamento para cartão ${maskedCard}`);

            const paymentStatus = String(cardNumber).startsWith(settings.approvedCardPrefix)
                ? PAYMENT_STATUS.PAID
                : PAYMENT_STATUS.DENIED;

            if (paymentStatus === PAYMENT_STATUS.DENIED) {
                return res.status(400).send('Pagamento recusado');
            }

            const enrollmentId = await this.enrollmentModel.createEnrollmentWithPaymentAndAudit({
                userId,
                courseId: course.id,
                amount: course.price,
                status: paymentStatus
            });

            auditCache.set(`last_checkout_${userId}`, course.title);
            return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        } catch (err) {
            return next(err);
        }
    }
}

module.exports = CheckoutController;
