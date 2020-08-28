import os
from flask import Flask, request, abort, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  app.secret_key = 'super secret key'
  setup_db(app)
  
  cors = CORS(app, resources={r"/questions/*": {"origins": "*"}})

  # CORS Headers 
  @app.after_request
  def after_request(response):
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,true")
    response.headers.add("Access-Control-Allow-Methods", "GET,PATCH,POST,DELETE,OPTIONS")
    return response

  @app.route('/categories')
  def retrieve_categories():
    categories = Category.query.order_by(Category.id).all()
    formatted_categories = [category.format() for category in categories]

    if len(categories) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'categories': formatted_categories
    })


  @app.route('/questions')
  def retrieve_questions():
    questions = Question.query.order_by(Question.id).all()
    categories = Category.query.order_by(Category.id).all()
    formatted_categories = [category.format() for category in categories]
    current_questions = paginate_questions(request, questions)

    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'categories': formatted_categories,
      'current_category': None,
      'total_questions': len(Question.query.all())
    })

  @app.route("/questions/<int:question_id>", methods=["DELETE"])
  def delete_question(question_id):
    try:
      question = Question.query.get(question_id)

      if question is None:
        abort(404)

      question.delete()
      return jsonify({
        'success': True,
        'deleted': question_id,
      })

    except:
      abort(404)

  @app.route("/questions", methods=["POST"])
  def add_question():
    body = request.get_json()
    question = body.get("question", "")
    answer = body.get("answer", "")
    category = body.get("category", "")
    difficulty = body.get("difficulty", "")
    
    try:
      question = Question(question = question, answer = answer, category = category, difficulty = difficulty)
      question.insert()

      return jsonify({
        'success': True,
        'created': question.id
      })

    except:
      abort(422)

  @app.route("/questions/search", methods=["POST"])
  def search_questions():
    search_term = request.get_json().get("search_term", "")

    try:
      questions = Question.query.filter(Question.question.ilike('%' + search_term + '%')).all()
      current_questions = paginate_questions(request, questions) if len(questions) > 0 else []

      if len(current_questions) == 0:
        abort(404)
      
      print(len(current_questions))

      return jsonify({
        'success': True,
        'questions': current_questions,
        'current_category': None,
        'total_questions': len(Question.query.all())
      })
    except:
      abort(404)

  @app.route("/categories/<int:category_id>/questions")
  def get_questions_by_category(category_id):
    questions = Question.query.filter(Question.category == str(category_id)).all()
    categories = Category.query.order_by(Category.id).all()
    current_category = Category.query.get(category_id)
    current_category = current_category.format() if current_category is not None else None
    formatted_categories = [category.format() for category in categories] if len(categories) > 0 else []
    current_questions = paginate_questions(request, questions) if len(questions) > 0 else []

    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'categories': formatted_categories,
      'current_category': current_category,
      'total_questions': len(Question.query.all())
    })


  @app.route("/quizzes", methods=["POST"])
  def get_quiz_quetion():
    body = request.get_json()
    previous_questions = body.get("previous_questions", "")
    quiz_category = body.get("quiz_category", "")

    if 'previous_questions' in session:
      SAVED_PREVIOUS_QUESTIONS = session.get('previous_questions')
    else:
      session['previous_questions'] = []
      SAVED_PREVIOUS_QUESTIONS = []

    print(session.get('previous_questions'))
    print(SAVED_PREVIOUS_QUESTIONS)
    
    try:
      if not quiz_category:
        questions = Question.query.all()
      else:
        questions = Question.query.filter(Question.category == str(quiz_category)).all()

      if not previous_questions: 
        session['previous_questions'] = []
        SAVED_PREVIOUS_QUESTIONS = []

      formatted_questions = [question.format() for question in questions]
      filtered_questions = [ question for question in formatted_questions if question.get("id") not in SAVED_PREVIOUS_QUESTIONS ]
      random_question = random.choice(filtered_questions) if len(filtered_questions) > 0 else None
      if len(filtered_questions) > 0:
        SAVED_PREVIOUS_QUESTIONS.append(random_question.get("id"))
        session['previous_questions'] = SAVED_PREVIOUS_QUESTIONS

      
      return jsonify({
        'success': True,
        'question': random_question
      })
    except:
      abort(422)
        

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": "resource not found"
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "unprocessable"
    }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": "bad request"
    }), 400

  @app.errorhandler(405)
  def not_allowed(error):
    return jsonify({
      "success": False, 
      "error": 405,
      "message": "method not allowed"
    }), 405
  
  return app

    