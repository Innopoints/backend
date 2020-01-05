INSERT INTO accounts (full_name, "group", email, telegram_username, is_admin)
	VALUES ('Admin', 'admin', 'admin@innopolis.university', null, true);
INSERT INTO accounts (full_name, "group", email, telegram_username, is_admin)
	VALUES ('Events department', 'projects_creator', 'events@innopolis.university', null, false);
INSERT INTO accounts (full_name, "group", email, telegram_username, is_admin)
	VALUES ('Student 1', 'student', 'student1@innopolis.university', 'a_student', false);
INSERT INTO accounts (full_name, "group", email, telegram_username, is_admin)
	VALUES ('Student 2', 'student', 'student2@innopolis.university', 'another_student', false);

INSERT INTO projects (name, image_id, creation_time, organizer, creator_email, admin_feedback, review_status, lifetime_stage)
	VALUES ('Some Olympiad', null, NOW(), 'Olympiad department', 'events@innopolis.university', null, null, 'draft');
INSERT INTO projects (name, image_id, creation_time, organizer, creator_email, admin_feedback, review_status, lifetime_stage)
	VALUES ('World Olympiad in something', null, NOW() - INTERVAL'1 Month', 'Olympiad department', 'events@innopolis.university', 'Good job', 'approved', 'finished');
INSERT INTO projects (name, image_id, creation_time, organizer, creator_email, admin_feedback, review_status, lifetime_stage)
	VALUES ('Christmas party', null, NOW() - INTERVAL'2 DAYS', 'Student Affairs', 'events@innopolis.university', null, null, 'ongoing');

INSERT INTO activities (name, description, start_date, end_date, project_id, working_hours, reward_rate, fixed_reward, people_required, telegram_required, application_deadline, feedback_questions)
	VALUES ('Manage something', null, NOW() + INTERVAL'10 DAYS', NOW() + INTERVAL'14 DAYS', 1, 5, 70, false, 13, true, NOW() + INTERVAL'1 WEEK', '{}');
INSERT INTO activities (name, description, start_date, end_date, project_id, working_hours, reward_rate, fixed_reward, people_required, telegram_required, application_deadline, feedback_questions)
	VALUES ('Catering', 'FOOD!!', NOW() + INTERVAL'12 DAYS', NOW() + INTERVAL'14 DAYS', 1, 3, 70, false, 5, false, NOW() + INTERVAL'1 WEEK', ARRAY['How was the food?']);
INSERT INTO activities (name, description, start_date, end_date, project_id, working_hours, reward_rate, fixed_reward, people_required, telegram_required, application_deadline, feedback_questions)
	VALUES ('Prepare laptops', 'obvious?', NOW() - INTERVAL'10 DAYS', NOW() - INTERVAL'8 DAYS', 2, 1, 100, true, 4, true, NOW() - INTERVAL'2 WEEKS', ARRAY['How are you?']);
INSERT INTO activities (name, description, start_date, end_date, project_id, working_hours, reward_rate, fixed_reward, people_required, telegram_required, application_deadline, feedback_questions)
	VALUES ('Decorate', 'Ornaments and stuff', NOW() - INTERVAL'1 DAY', NOW() + INTERVAL'3 DAYS', 3, 8, 70, false, 10, false, NOW() - INTERVAL'3 DAYS', ARRAY['Was it easy?', 'Should we start earlier next time?']);

INSERT INTO applications (applicant_email, activity_id, comment, application_time, telegram_username, status, actual_hours)
	VALUES ('student1@innopolis.university', 3, 'Please accept me', NOW() - INTERVAL'3 WEEKS', null, 'approved', 2);
INSERT INTO applications (applicant_email, activity_id, comment, application_time, telegram_username, status, actual_hours)
	VALUES ('student2@innopolis.university', 3, 'I''m the best', NOW() - INTERVAL'3 WEEKS', 'what?', 'rejected', null);
INSERT INTO applications (applicant_email, activity_id, comment, application_time, telegram_username, status, actual_hours)
	VALUES ('student1@innopolis.university', 4, 'I love christmas!', NOW(), null, 'pending', null);

INSERT INTO activity_competence (activity_id, competence_id)
	VALUES (1, 2), (1, 5), (1, 9);
INSERT INTO activity_competence (activity_id, competence_id)
	VALUES (2, 2);
INSERT INTO activity_competence (activity_id, competence_id)
	VALUES (3, 2), (3, 7);
INSERT INTO activity_competence (activity_id, competence_id)
	VALUES (4, 1), (4, 5), (4, 3), (4, 9);

INSERT INTO reports (application_id, rating, content, reporter_email)
	VALUES (1, 4, 'Great volunteer. Nice to work with.', 'events@innopolis.university');

INSERT INTO products (name, type, description, price, addition_time)
	VALUES ('ASCII Whale', 'T-shirt', '', 1337, NOW());
INSERT INTO products (name, type, description, price, addition_time)
	VALUES ('Innopolis University', 'stickers', 'To stick on your laptop', 200, NOW());
INSERT INTO products (name, type, description, price, addition_time)
	VALUES ('Breakfast + Lunch + Dinner, 7 days', 'meal plan', 'A meal plan for any canteen, available on work days. Lasts for a month.\n\nPurchase day:\n  •  1st – 14th: applies to the current month\n  •  15th – 31st: applies to the next month', 5000, NOW());

INSERT INTO varieties (product_id, size, color)
	VALUES (1, 'XS', '000000');
INSERT INTO varieties (product_id, size, color)
	VALUES (1, 'XS', '387800');
INSERT INTO varieties (product_id, size, color)
	VALUES (1, 'M', '387800');
INSERT INTO varieties (product_id, size, color)
	VALUES (2, null, 'FFFFFF');
INSERT INTO varieties (product_id, size, color)
	VALUES (2, null, '1A17D5');
INSERT INTO varieties (product_id, size, color)
	VALUES (3, null, null);

INSERT INTO stock_changes (amount, "time", status, account_email, variety_id)
	VALUES (20, NOW(), 'carried_out', 'admin@innopolis.university', 1);
INSERT INTO stock_changes (amount, "time", status, account_email, variety_id)
	VALUES (30, NOW(), 'carried_out', 'admin@innopolis.university', 3);
INSERT INTO stock_changes (amount, "time", status, account_email, variety_id)
	VALUES (100, NOW(), 'carried_out', 'admin@innopolis.university', 4);
INSERT INTO stock_changes (amount, "time", status, account_email, variety_id)
	VALUES (99999, NOW(), 'carried_out', 'admin@innopolis.university', 6);
INSERT INTO stock_changes (amount, "time", status, account_email, variety_id)
	VALUES (-1, NOW(), 'pending', 'student1@innopolis.university', 2);
INSERT INTO stock_changes (amount, "time", status, account_email, variety_id)
	VALUES (-1, NOW(), 'ready_for_pickup', 'student2@innopolis.university', 1);
INSERT INTO stock_changes (amount, "time", status, account_email, variety_id)
	VALUES (-5, NOW(), 'rejected', 'student1@innopolis.university', 6);

INSERT INTO transactions (account_email, change, stock_change_id, feedback_id)
	VALUES ('student1@innopolis.university', 5321, null, null);
INSERT INTO transactions (account_email, change, stock_change_id, feedback_id)
	VALUES ('student2@innopolis.university', 1234, null, null);
INSERT INTO transactions (account_email, change, stock_change_id, feedback_id)
	VALUES ('student1@innopolis.university', -1337, 5, null);
INSERT INTO transactions (account_email, change, stock_change_id, feedback_id)
	VALUES ('student2@innopolis.university', -1337, 6, null);
-- INSERT INTO transactions (account_email, change, stock_change_id, feedback_id)
-- 	VALUES ('student1@innopolis.university', 0, 7, null);

INSERT INTO project_moderation (project_id, account_email)
	VALUES (1, 'admin@innopolis.university'), (1, 'events@innopolis.university');
INSERT INTO project_moderation (project_id, account_email)
	VALUES (2, 'student1@innopolis.university'), (2, 'events@innopolis.university');
INSERT INTO project_moderation (project_id, account_email)
	VALUES (3, 'student2@innopolis.university'), (3, 'events@innopolis.university');

INSERT INTO feedback (application_id, answers, "time")
	VALUES (1, ARRAY['fine'], NOW());
