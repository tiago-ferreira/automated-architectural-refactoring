function errorHandler(err, req, res, next) {
    console.error('[ERROR] Erro não tratado na requisição:', err.message);
    if (res.headersSent) {
        return next(err);
    }
    const statusCode = err.statusCode || 500;
    return res.status(statusCode).json({
        error: err.expose ? err.message : 'Erro interno do servidor'
    });
}

module.exports = errorHandler;
