class UserController {
    constructor({ userModel }) {
        this.userModel = userModel;
    }

    async deleteUser(req, res, next) {
        try {
            const userId = Number(req.params.id);
            if (!Number.isInteger(userId) || userId <= 0) {
                return res.status(400).send('ID de usuário inválido');
            }

            await this.userModel.deleteByIdWithCascade(userId);
            return res.status(200).send('Usuário e registros dependentes removidos com sucesso.');
        } catch (err) {
            return next(err);
        }
    }
}

module.exports = UserController;
