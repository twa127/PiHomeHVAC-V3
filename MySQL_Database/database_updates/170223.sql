ALTER TABLE `system_controller` ADD COLUMN IF NOT EXISTS `pid` char(50) COLLATE utf16_bin;
ALTER TABLE `system_controller` ADD COLUMN IF NOT EXISTS `pid_running_since` char(50) COLLATE utf16_bin;