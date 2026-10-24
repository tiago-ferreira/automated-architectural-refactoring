class ReportController {
    constructor({ reportModel }) {
        this.reportModel = reportModel;
    }

    async getFinancialReport(req, res, next) {
        try {
            const report = await this.reportModel.getFinancialReport();
            return res.status(200).json(report);
        } catch (err) {
            return next(err);
        }
    }
}

module.exports = ReportController;
