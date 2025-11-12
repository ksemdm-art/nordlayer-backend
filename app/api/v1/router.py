from fastapi import APIRouter
from .endpoints import projects, orders, articles, services, categories, auth, files, content, users, cms, colors, reviews, contact, webhooks, cache, health

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(cms.router, prefix="/cms", tags=["cms"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(services.router, prefix="/services", tags=["services"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(colors.router, prefix="/colors", tags=["colors"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(contact.router, prefix="/contact", tags=["contact"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
api_router.include_router(health.router, tags=["monitoring"])