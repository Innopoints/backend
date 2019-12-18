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

-- TODO: products and varieties. project moderators. feedback. stock_changes. transactions.
