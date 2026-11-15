from app.database.base import Base, SessionLocal
from app.models import *
from app.models.exam_category import ExamCategory
from app.core.security import hash_password
import json, logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

def init_db():
    # Import engine at runtime to respect any monkey‑patching in tests
    from app.database.base import engine as db_engine
    if db_engine.dialect.name == "sqlite":
        for _table in Base.metadata.tables.values():
            _table.schema = None
    if db_engine.dialect.name == "postgresql":
        with db_engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth_security"))
    Base.metadata.create_all(bind=db_engine)
    db = SessionLocal()
    try:
        categories = _ensure_exam_categories(db)

        if db.query(Subject).count() > 0:
            general_category = categories["general-learning"]
            subjects = db.query(Subject).filter(
                Subject.exam_category_id.is_(None)
            ).all()

            for subject in subjects:
                subject.exam_category_id = general_category.id

            db.commit()
            logger.info("Database already seeded; exam categories verified")
            return

        _seed_all(db, categories)
        logger.info("Database seeded successfully")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def _ensure_exam_categories(db):
    categories_data = [
        {
            "name": "General Learning",
            "slug": "general-learning",
            "description": "Explore general learning subjects",
            "order": 1,
        },
        {
            "name": "IIT JEE",
            "slug": "jee",
            "description": "Prepare for IIT JEE",
            "order": 2,
        },
        {
            "name": "NEET UG",
            "slug": "neet",
            "description": "Prepare for NEET UG",
            "order": 3,
        },
    ]

    categories = {}

    for item in categories_data:
        category = db.query(ExamCategory).filter(
            ExamCategory.slug == item["slug"]
        ).first()

        if category is None:
            category = ExamCategory(
                name=item["name"],
                slug=item["slug"],
                description=item["description"],
                display_order=item["order"],
                is_active=True,
            )
            db.add(category)
            db.flush()
        else:
            category.name = item["name"]
            category.description = item["description"]
            category.display_order = item["order"]
            category.is_active = True

        categories[item["slug"]] = category

    db.flush()
    return categories


def _seed_all(db, categories):
    admin = User(
        email="admin@learnsphere.ai",
        username="admin",
        hashed_password=hash_password("Admin123!"),
        full_name="LearnSphere Admin",
        role="admin"
    )
    db.add(admin)
    db.flush()
    admin_profile = StudentProfile(user_id=admin.id, xp_total=9999, current_streak=100)
    db.add(admin_profile)
    
    subjects_data = [
        {"name": "Mathematics", "slug": "mathematics", "description": "Master numbers, patterns, and mathematical reasoning", "icon": "calculator", "color": "#6366f1", "order": 1},
        {"name": "Science", "slug": "science", "description": "Explore the physical universe through mechanics, energy, and chemistry", "icon": "flask", "color": "#10b981", "order": 2},
        {"name": "Computer Science", "slug": "computer-science", "description": "Learn algorithms, Python programming, and computational logic", "icon": "code", "color": "#f59e0b", "order": 3},
        {"name": "Logical Reasoning", "slug": "logical-reasoning", "description": "Sharpen analytical problem-solving and deductive thinking", "icon": "brain", "color": "#ef4444", "order": 4},
    ]
    
    subjects = {}
    for sd in subjects_data:
        s = Subject(name=sd["name"], slug=sd["slug"], description=sd["description"],
                    icon=sd["icon"], color=sd["color"], display_order=sd["order"],
                    exam_category_id=categories["general-learning"].id)
        db.add(s)
        db.flush()
        subjects[sd["slug"]] = s
    
    _seed_math(db, subjects["mathematics"])
    _seed_science(db, subjects["science"])
    _seed_cs(db, subjects["computer-science"])
    _seed_logic(db, subjects["logical-reasoning"])
    
    achievements_data = [
        {"name": "First Step", "description": "Complete your first lesson", "icon": "🎯", "xp": 50, "criteria": {"type": "first_lesson"}},
        {"name": "Week Warrior", "description": "Maintain a 7-day learning streak", "icon": "🔥", "xp": 200, "criteria": {"type": "streak", "value": 7}},
        {"name": "XP Collector", "description": "Earn 500 total XP", "icon": "⭐", "xp": 100, "criteria": {"type": "xp", "value": 500}},
        {"name": "Scholar", "description": "Earn 1000 total XP", "icon": "🏆", "xp": 200, "criteria": {"type": "xp", "value": 1000}},
        {"name": "Dedicated Learner", "description": "Maintain a 30-day streak", "icon": "💪", "xp": 500, "criteria": {"type": "streak", "value": 30}},
    ]
    for ad in achievements_data:
        a = Achievement(name=ad["name"], description=ad["description"], icon=ad["icon"], xp_reward=ad["xp"], criteria=json.dumps(ad["criteria"]))
        db.add(a)
    
    db.commit()

def _seed_math(db, subject):
    c1 = Course(subject_id=subject.id, title="Algebra Fundamentals", slug="algebra-fundamentals",
                description="Master algebraic thinking, equations, and visual mathematical problem solving.",
                difficulty="beginner", estimated_hours=8.0, thumbnail_color="#6366f1")
    db.add(c1)
    db.flush()
    
    m1 = Module(course_id=c1.id, title="Variables & Linear Equations", description="Understanding unknowns and equation balancing", display_order=1)
    db.add(m1)
    db.flush()
    
    l1 = Lesson(module_id=m1.id, title="The Essence of Variables", description="Understand what variables really represent",
                lesson_type="concept", estimated_minutes=15, display_order=1,
                content=json.dumps({
                    "blocks": [
                        {"type": "text", "content": "A **variable** is a symbol (like $x$ or $y$) representing an unknown or dynamically changing quantity."},
                        {"type": "text", "content": "Think of a variable as a labeled container. When balancing an equation like $x + 5 = 12$, we determine what quantity inside the container makes both sides equal."},
                        {"type": "example", "content": "If $x = 7$, then $7 + 5 = 12$. The balance is maintained!"}
                    ]
                }))
    db.add(l1)
    db.flush()
    
    q1 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="If $3x - 4 = 11$, what is the value of $x$?",
                  question_type="numerical", difficulty="beginner",
                  correct_answer="5",
                  explanation="Add 4 to both sides: $3x = 15$. Divide both sides by 3: $x = 5$.",
                  hint="First isolate the term with $x$ by adding 4 to both sides.",
                  tags=json.dumps(["Linear Equations", "Algebra"]))
    db.add(q1)
    
    q2 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="Which of the following describes an algebraic equation?",
                  question_type="multiple_choice", difficulty="beginner",
                  correct_answer="b",
                  explanation="An equation explicitly states that two mathematical expressions are equal using an '=' sign.",
                  hint="Look for the requirement of equality.",
                  tags=json.dumps(["Algebra Basics"]))
    db.add(q2)
    db.flush()
    opts = [
        ("A collection of numbers without symbols", False, 0),
        ("A mathematical statement that two expressions are equal", True, 1),
        ("An operation that only multiplies values", False, 2),
        ("A graphical representation of shapes", False, 3)
    ]
    for text, corr, order in opts:
        db.add(QuestionOption(question_id=q2.id, option_text=text, is_correct=corr, display_order=order))

    q3 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="What is the positive solution to $x^2 - 7x + 12 = 0$ where $x > 3$?",
                  question_type="numerical", difficulty="intermediate",
                  correct_answer="4",
                  explanation="Factor the quadratic: $(x - 3)(x - 4) = 0$. The roots are $x = 3$ and $x = 4$. For $x > 3$, the answer is 4.",
                  hint="Factor the quadratic into two binomials $(x - a)(x - b) = 0$.",
                  tags=json.dumps(["Quadratic Equations", "Algebra"]))
    db.add(q3)

    q4 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="A fair coin is tossed twice. What is the probability of getting at least one Head?",
                  question_type="multiple_choice", difficulty="beginner",
                  correct_answer="c",
                  explanation="Possible outcomes are {HH, HT, TH, TT}. Outcomes with at least one Head are {HH, HT, TH} (3 out of 4), so probability is 3/4.",
                  hint="Count the total equally likely outcomes: HH, HT, TH, TT.",
                  tags=json.dumps(["Probability", "Combinatorics"]))
    db.add(q4)
    db.flush()
    opts_prob = [
        ("1/4", False, 0),
        ("1/2", False, 1),
        ("3/4", True, 2),
        ("1", False, 3)
    ]
    for text, corr, order in opts_prob:
        db.add(QuestionOption(question_id=q4.id, option_text=text, is_correct=corr, display_order=order))

def _seed_science(db, subject):
    c1 = Course(subject_id=subject.id, title="Physics: Mechanics & Motion", slug="physics-mechanics",
                description="Explore the laws of motion, inertia, forces, and gravitational acceleration.",
                difficulty="beginner", estimated_hours=10.0, thumbnail_color="#10b981")
    db.add(c1)
    db.flush()
    
    m1 = Module(course_id=c1.id, title="Newtonian Mechanics", description="Laws of motion and equilibrium", display_order=1)
    db.add(m1)
    db.flush()
    
    l1 = Lesson(module_id=m1.id, title="Newton's Laws of Motion", description="Inertia, acceleration, and action-reaction",
                lesson_type="concept", estimated_minutes=20, display_order=1,
                content=json.dumps({
                    "blocks": [
                        {"type": "text", "content": "Newton's First Law states: An object remains at rest, or in uniform motion along a straight line, unless acted upon by a net external force."},
                        {"type": "text", "content": "Formula for force: $F = ma$ where $m$ is mass in kilograms and $a$ is acceleration in $m/s^2$."},
                        {"type": "example", "content": "If a $10\\text{ kg}$ object accelerates at $3\\text{ m/s}^2$, the net force applied is $F = 10 \\times 3 = 30\\text{ Newtons}$."}
                    ]
                }))
    db.add(l1)
    db.flush()
    
    q1 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="A 5 kg block is accelerated at 4 m/s². What is the net force applied in Newtons?",
                  question_type="numerical", difficulty="beginner",
                  correct_answer="20",
                  explanation="Using $F = ma$: $F = 5 \\times 4 = 20\\text{ N}$.",
                  hint="Multiply mass by acceleration.",
                  tags=json.dumps(["Newton's Second Law", "Mechanics"]))
    db.add(q1)
    
    q2 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="In the absence of friction and gravity, a moving object will eventually stop on its own.",
                  question_type="true_false", difficulty="beginner",
                  correct_answer="false",
                  explanation="According to Newton's First Law, without any opposing external force (like friction), the object will continue moving indefinitely at constant velocity.",
                  hint="Recall the principle of inertia.",
                  tags=json.dumps(["Inertia", "Mechanics"]))
    db.add(q2)

    q3 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="If a 2 kg object is moving at a velocity of 6 m/s, what is its kinetic energy in Joules ($KE = \\frac{1}{2}mv^2$)?",
                  question_type="numerical", difficulty="intermediate",
                  correct_answer="36",
                  explanation="Using $KE = 0.5 \\times m \\times v^2 = 0.5 \\times 2 \\times 36 = 36\\text{ Joules}$.",
                  hint="Square the velocity first, then multiply by half the mass.",
                  tags=json.dumps(["Kinetic Energy", "Work & Energy"]))
    db.add(q3)

    q4 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="According to Ohm's Law ($V = IR$), if the voltage is 24V and resistance is 8 Ohms, what is the current in Amperes?",
                  question_type="numerical", difficulty="beginner",
                  correct_answer="3",
                  explanation="Using $I = V / R = 24 / 8 = 3\\text{ Amperes}$.",
                  hint="Divide the voltage by the resistance.",
                  tags=json.dumps(["Electricity & Circuits", "Physics"]))
    db.add(q4)

def _seed_cs(db, subject):
    c1 = Course(subject_id=subject.id, title="Python Programming Fundamentals", slug="python-fundamentals",
                description="Interactive hands-on Python: variables, data structures, loops, and problem solving.",
                difficulty="beginner", estimated_hours=12.0, thumbnail_color="#f59e0b")
    db.add(c1)
    db.flush()
    
    m1 = Module(course_id=c1.id, title="Control Structures & Lists", description="Sequences and logic flow in Python", display_order=1)
    db.add(m1)
    db.flush()
    
    l1 = Lesson(module_id=m1.id, title="Lists and Iteration", description="Managing collections of data with for loops",
                lesson_type="coding", estimated_minutes=25, display_order=1,
                content=json.dumps({
                    "blocks": [
                        {"type": "text", "content": "In Python, a **list** is an ordered, mutable sequence of items. Lists are zero-indexed."},
                        {"type": "code", "language": "python", "content": "fruits = ['apple', 'banana', 'cherry']\nfor index, fruit in enumerate(fruits):\n    print(f'{index}: {fruit}')"},
                        {"type": "text", "content": "Common methods include `.append(item)`, `.pop()`, and `len(list)`."}
                    ]
                }))
    db.add(l1)
    db.flush()
    
    q1 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="Given `nums = [10, 20, 30, 40]`, what is the value of `nums[2]`?",
                  question_type="numerical", difficulty="beginner",
                  correct_answer="30",
                  explanation="Python lists are 0-indexed: index 0 is 10, index 1 is 20, index 2 is 30.",
                  hint="Remember indexing starts at 0.",
                  tags=json.dumps(["Python", "Lists", "Indexing"]))
    db.add(q1)
    
    q2 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="Which Python keyword is used to define an immutable function?",
                  question_type="multiple_choice", difficulty="beginner",
                  correct_answer="a",
                  explanation="Functions are defined in Python using the `def` keyword.",
                  hint="Look for the standard three-letter keyword.",
                  tags=json.dumps(["Python Basics"]))
    db.add(q2)
    db.flush()
    opts = [
        ("def", True, 0),
        ("function", False, 1),
        ("fun", False, 2),
        ("lambda_func", False, 3)
    ]
    for text, corr, order in opts:
        db.add(QuestionOption(question_id=q2.id, option_text=text, is_correct=corr, display_order=order))

    q3 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="What is the worst-case time complexity of Binary Search on a sorted array of size $n$?",
                  question_type="multiple_choice", difficulty="intermediate",
                  correct_answer="b",
                  explanation="Binary Search repeatedly divides the search interval in half, yielding $O(\\log n)$ worst-case time complexity.",
                  hint="Think about how many times you can halve an array of size n.",
                  tags=json.dumps(["Algorithms", "Complexity Analysis"]))
    db.add(q3)
    db.flush()
    opts_algo = [
        ("O(1)", False, 0),
        ("O(log n)", True, 1),
        ("O(n)", False, 2),
        ("O(n^2)", False, 3)
    ]
    for text, corr, order in opts_algo:
        db.add(QuestionOption(question_id=q3.id, option_text=text, is_correct=corr, display_order=order))

    q4 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="In Python, which built-in function returns the number of elements in a sequence?",
                  question_type="multiple_choice", difficulty="beginner",
                  correct_answer="a",
                  explanation="The `len()` function returns the length of a sequence or collection in Python.",
                  hint="Look for the concise three-letter built-in.",
                  tags=json.dumps(["Python Basics", "Data Structures"]))
    db.add(q4)
    db.flush()
    opts_len = [
        ("len()", True, 0),
        ("size()", False, 1),
        ("count()", False, 2),
        ("length()", False, 3)
    ]
    for text, corr, order in opts_len:
        db.add(QuestionOption(question_id=q4.id, option_text=text, is_correct=corr, display_order=order))

def _seed_logic(db, subject):
    c1 = Course(subject_id=subject.id, title="Critical Thinking & Logic Puzzles", slug="critical-thinking",
                description="Master deductive deduction, conditional logic, truth tables, and pattern extrapolation.",
                difficulty="beginner", estimated_hours=6.0, thumbnail_color="#ef4444")
    db.add(c1)
    db.flush()
    
    m1 = Module(course_id=c1.id, title="Deductive Reasoning", description="Valid inferences vs logical fallacies", display_order=1)
    db.add(m1)
    db.flush()
    
    l1 = Lesson(module_id=m1.id, title="Conditional Logic: If-Then Reasoning", description="Implications, contrapositives, and valid deduction",
                lesson_type="concept", estimated_minutes=15, display_order=1,
                content=json.dumps({
                    "blocks": [
                        {"type": "text", "content": "A conditional statement has the form: **If P, then Q** ($P \\implies Q$)."},
                        {"type": "text", "content": "The **contrapositive** is: **If not Q, then not P** ($\\neg Q \\implies \\neg P$). The contrapositive is logically equivalent to the original statement."},
                        {"type": "example", "content": "'If it is raining, the grass is wet' is logically equivalent to 'If the grass is not wet, it is not raining'."}
                    ]
                }))
    db.add(l1)
    db.flush()
    
    q1 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="What is the next number in the pattern: 2, 5, 10, 17, 26, ?",
                  question_type="numerical", difficulty="intermediate",
                  correct_answer="37",
                  explanation="The differences between consecutive numbers are consecutive odd numbers: +3, +5, +7, +9, +11. So 26 + 11 = 37 (or $n^2 + 1$).",
                  hint="Look at the differences between adjacent terms: 3, 5, 7, 9...",
                  tags=json.dumps(["Sequences", "Pattern Recognition"]))
    db.add(q1)

    q2 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="All squares are rectangles. Some rectangles are red. Therefore, all squares are red.",
                  question_type="true_false", difficulty="intermediate",
                  correct_answer="false",
                  explanation="This is a logical fallacy. Knowing that some rectangles are red does not imply that squares (a subset of rectangles) are red.",
                  hint="Consider whether all subsets of rectangles must inherit properties possessed by only some rectangles.",
                  tags=json.dumps(["Deductive Logic", "Syllogisms"]))
    db.add(q2)

    q3 = Question(lesson_id=l1.id, subject_id=subject.id,
                  question_text="If Alex is taller than Brian, and Brian is taller than Chris, then Alex is taller than Chris.",
                  question_type="true_false", difficulty="beginner",
                  correct_answer="true",
                  explanation="By the transitivity of strict linear ordering (height), if A > B and B > C, then A > C.",
                  hint="Apply transitive reasoning across inequalities.",
                  tags=json.dumps(["Transitive Logic", "Logical Reasoning"]))
    db.add(q3)
