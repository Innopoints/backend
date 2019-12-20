INSERT INTO accounts (full_name, university_status, email, telegram_username, is_admin)
	VALUES ('Admin', 'admin', 'admin@innopolis.university', null, true);
INSERT INTO accounts (full_name, university_status, email, telegram_username, is_admin)
	VALUES ('Events department', 'projects_creator', 'events@innopolis.university', null, false);
INSERT INTO accounts (full_name, university_status, email, telegram_username, is_admin)
	VALUES ('Student 1', 'student', 'student1@innopolis.university', 'a_student', false);
INSERT INTO accounts (full_name, university_status, email, telegram_username, is_admin)
	VALUES ('Student 2', 'student', 'student2@innopolis.university', 'another_student', false);

INSERT INTO projects (id, name, image_id, creation_time, organizer, creator_email, admin_feedback, review_status, lifetime_stage)
	VALUES (1, 'Some Olympiad', null, NOW(), 'Olympiad department', 'events@innopolis.university', null, 'pending', 'draft');
INSERT INTO projects (id, name, image_id, creation_time, organizer, creator_email, admin_feedback, review_status, lifetime_stage)
	VALUES (2, 'World Olympiad in something', null, NOW() - INTERVAL'1 Month', 'Olympiad department', 'events@innopolis.university', 'Good job', 'approved', 'past');
INSERT INTO projects (id, name, image_id, creation_time, organizer, creator_email, admin_feedback, review_status, lifetime_stage)
	VALUES (3, 'Christmas party', null, NOW() - INTERVAL'2 DAYS', 'Student Affairs', 'events@innopolis.university', null, 'approved', 'ongoing');

INSERT INTO activities (id, name, description, start_date, end_date, project_id, working_hours, reward_rate, fixed_reward, people_required, telegram_required, application_deadline, feedback_questions)
	VALUES (1, 'Manage something', null, NOW() + INTERVAL'10 DAYS', NOW() + INTERVAL'14 DAYS', 1, 5, null, false, 13, true, NOW() + INTERVAL'1 WEEK', '{}');
INSERT INTO activities (id, name, description, start_date, end_date, project_id, working_hours, reward_rate, fixed_reward, people_required, telegram_required, application_deadline, feedback_questions)
	VALUES (2, 'Catering', 'FOOD!!', NOW() + INTERVAL'12 DAYS', NOW() + INTERVAL'14 DAYS', 1, 3, null, false, 5, false, NOW() + INTERVAL'1 WEEK', ARRAY['How was the food?']);
INSERT INTO activities (id, name, description, start_date, end_date, project_id, working_hours, reward_rate, fixed_reward, people_required, telegram_required, application_deadline, feedback_questions)
	VALUES (3, 'Prepare laptops', 'obvious?', NOW() - INTERVAL'10 DAYS', NOW() - INTERVAL'8 DAYS', 2, null, 100, true, 4, true, NOW() - INTERVAL'2 WEEKS', '{}');
INSERT INTO activities (id, name, description, start_date, end_date, project_id, working_hours, reward_rate, fixed_reward, people_required, telegram_required, application_deadline, feedback_questions)
	VALUES (4, 'Decorate', 'Ornaments and stuff', NOW() - INTERVAL'1 DAY', NOW() + INTERVAL'3 DAYS', 3, 8, null, false, 10, false, NOW() - INTERVAL'3 DAYS', ARRAY['Was it easy?', 'Should we start earlier next time?']);

INSERT INTO applications (id, applicant_email, activity_id, comment, application_time, telegram_username, status, actual_hours)
	VALUES (1, 'student1@innopolis.university', 3, 'Please accept me', NOW() - INTERVAL'3 WEEKS', null, 'approved', 2);
INSERT INTO applications (id, applicant_email, activity_id, comment, application_time, telegram_username, status, actual_hours)
	VALUES (2, 'student2@innopolis.university', 3, 'I''m the best', NOW() - INTERVAL'3 WEEKS', 'what?', 'rejected', null);
INSERT INTO applications (id, applicant_email, activity_id, comment, application_time, telegram_username, status, actual_hours)
	VALUES (3, 'student1@innopolis.university', 4, 'I love christmas!', NOW(), null, 'pending', null);

INSERT INTO activity_competence (activity_id, competence_id) 
	VALUES (1, 2), (1, 5), (1, 9);
INSERT INTO activity_competence (activity_id, competence_id) 
	VALUES (3, 2), (3, 7);
INSERT INTO activity_competence (activity_id, competence_id) 
	VALUES (4, 1), (4, 5), (4, 3), (4, 9);

INSERT INTO reports (id, application_id, rating, content)
	VALUES (1, 1, 4, 'Great volunteer. Nice to work with.');

INSERT INTO products (id, name, type, description, price, addition_time)
	VALUES (1, 'T-shirt', 'clothes', '', 1337, NOW());
INSERT INTO products (id, name, type, description, price, addition_time)
	VALUES (2, 'stickers', 'collectibles', 'to stick on your laptop', 200, NOW());
INSERT INTO products (id, name, type, description, price, addition_time)
	VALUES (3, 'Meal plan (7 days)', 'food', 'Lunch 7days/week 1 month effective next month', 5000, NOW());

INSERT INTO varieties (id, product_id, size_id, color_value)
	VALUES (1, 1, 'XS', '000000');
INSERT INTO varieties (id, product_id, size_id, color_value)
	VALUES (2, 1, 'XS', '387800');
INSERT INTO varieties (id, product_id, size_id, color_value)
	VALUES (3, 1, 'M', '387800');
INSERT INTO varieties (id, product_id, size_id, color_value)
	VALUES (4, 2, null, 'FFFFFF');
INSERT INTO varieties (id, product_id, size_id, color_value)
	VALUES (5, 2, null, '1A17D5');
INSERT INTO varieties (id, product_id, size_id, color_value)
	VALUES (6, 3, null, null);

INSERT INTO stock_changes (id, amount, time, status, account_email, variety_id)
	VALUES (1, 20, NOW(), 'carried_out', 'admin@innopolis.university', 1);
INSERT INTO stock_changes (id, amount, time, status, account_email, variety_id)
	VALUES (2, 30, NOW(), 'carried_out', 'admin@innopolis.university', 3);
INSERT INTO stock_changes (id, amount, time, status, account_email, variety_id)
	VALUES (3, 100, NOW(), 'carried_out', 'admin@innopolis.university', 4);
INSERT INTO stock_changes (id, amount, time, status, account_email, variety_id)
	VALUES (4, 99999, NOW(), 'carried_out', 'admin@innopolis.university', 6);
INSERT INTO stock_changes (id, amount, time, status, account_email, variety_id)
	VALUES (5, -1, NOW(), 'pending', 'student1@innopolis.university', 2);
INSERT INTO stock_changes (id, amount, time, status, account_email, variety_id)
	VALUES (6, -1, NOW(), 'ready_for_pickup', 'student2@innopolis.university', 1);
INSERT INTO stock_changes (id, amount, time, status, account_email, variety_id)
	VALUES (7, -5, NOW(), 'rejected', 'student1@innopolis.university', 6);

INSERT INTO transactions (id, account_email, change, stock_change_id, feedback_id)
	VALUES (1, 'student1@innopolis.university', 5321, null, null);
INSERT INTO transactions (id, account_email, change, stock_change_id, feedback_id)
	VALUES (2, 'student2@innopolis.university', 1234, null, null);
INSERT INTO transactions (id, account_email, change, stock_change_id, feedback_id)
	VALUES (3, 'student1@innopolis.university', -1337, 5, null);
INSERT INTO transactions (id, account_email, change, stock_change_id, feedback_id)
	VALUES (4, 'student1@innopolis.university', 0, 7, null);
INSERT INTO transactions (id, account_email, change, stock_change_id, feedback_id)
	VALUES (5, 'student2@innopolis.university', -1337, 6, null);

INSERT INTO project_moderation (project_id, account_email)
	VALUES (1, 'admin@innopolis.university');
INSERT INTO project_moderation (project_id, account_email)
	VALUES (2, 'student1@innopolis.university');
INSERT INTO project_moderation (project_id, account_email)
	VALUES (3, 'student2@innopolis.university');

INSERT INTO feedback (id, application_id, answers)
	VALUES (1, 1, '[{"question": "how are you", "answer": "fine"}]');
