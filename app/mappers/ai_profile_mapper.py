from app.enums.app_enum import ActivityLevelEnum, GoalTypeEnum


ACTIVITY_TO_EXPERIENCE = {
    ActivityLevelEnum.sedentary: "beginner",
    ActivityLevelEnum.lightly_active: "beginner",
    ActivityLevelEnum.moderately_active: "intermediate",
    ActivityLevelEnum.very_active: "advanced",
}

ACTIVITY_TO_DAYS = {
    ActivityLevelEnum.sedentary: 3,
    ActivityLevelEnum.lightly_active: 4,
    ActivityLevelEnum.moderately_active: 5,
    ActivityLevelEnum.very_active: 6,
}

ACTIVITY_TO_SESSION_DURATION = {
    ActivityLevelEnum.sedentary: 45,
    ActivityLevelEnum.lightly_active: 60,
    ActivityLevelEnum.moderately_active: 75,
    ActivityLevelEnum.very_active: 90,
}

GOAL_MAPPING = {
    GoalTypeEnum.lose_weight: "fat_loss",
    GoalTypeEnum.maintain: "maintenance",
    GoalTypeEnum.gain_weight: "hypertrophy",
}
