"""توافق خلفي: الوكيل العام القديم أصبح وكيل الاختبارات.

استخدم `app.graph.nodes.quiz_agent.make_quiz_agent_node` مباشرة.
هذا الملف يبقى مؤقتا حتى تكتمل إعادة التسمية في كل الاستيرادات.
"""

from app.graph.nodes.quiz_agent import QUIZ_AGENT_SYSTEM, make_quiz_agent_node

AGENT_SYSTEM = QUIZ_AGENT_SYSTEM


def make_agent_node(model):  # type: ignore[no-untyped-def]
    """اسم قديم ← وكيل الاختبارات. لا تستخدمه في كود جديد."""
    return make_quiz_agent_node(model)


__all__ = ["AGENT_SYSTEM", "make_agent_node"]
