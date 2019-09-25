#####################################################
# Utils file for TASKS management                   #
#                                                   #
# Methods:                                          #
#       - getNumberActiveTask()                     #
#       - getTaskList()                             #
#       - cancelAllTask()                           #
#####################################################

# Modules required
from subprocess import check_output     # Run windows command from python
import re                               # Regex


def getNumberActiveTask(verbose=False):
    """ Return the number of task RUNNING + READY 
        The sum must be bellow 3000 (GEE restriction)
    """
    cmd_out = check_output("earthengine task list", shell=True)  \
                        .decode("utf-8")
    n = cmd_out.count('READY') + cmd_out.count('RUNNING')
    if verbose: print("Number RUNNING and READY tasks: " + str(n))
    return n


def getTaskList(verbose=False, all=False):
    """ Return all the current task RUNNING or READY (waiting)
    Arguments
        :param verbose=False: 
    """
    cmd_out = check_output("earthengine task list", shell=True)  \
                        .decode("utf-8")
    tasks_list = cmd_out.replace('\n', '') \
                        .replace('\r', '') \
                        .split("---")

    tasks = []
    keys = ["id_task", "Operation", "Description", "Status"]

    for task in tasks_list:
        values = re.split(r'\s{2,}', task)[:-1]
        if len(values) == 4:
            if not all:
                if values[3] == "READY" or values[3] == "RUNNING":
                    tasks.append({k: v for k, v in zip(keys, values) if k != ""})
            else:
                tasks.append({k: v for k, v in zip(keys, values) if k != ""})

    # tasks.pop('', None)
    if verbose:
        print(tasks)
        print("READY task:", cmd_out.count('READY'))
        print("RUNNING task:", cmd_out.count('RUNNING'))
    return tasks


def cancelAllTask(verbose=False, task_list=None):
    """ Cancel all the active task (READY and RUNNING)
        The commann seems to fail if more than 32 arguments (task_id) are given at the same time
    """
    # Max argument number given to one command
    nb_max = 32
    
    if task_list is None:
        task_list = getTaskList(verbose=False)
        task_list = [task["id_task"] for task in task_list]
    total = len(task_list)
    counter = 0

    # Reshape as 2d list
    task_list = [task_list[i:i + nb_max] for i in range(0, len(task_list), nb_max)]
    
    if verbose:
        print("{:-<100}\n|{:^98}|\n{:-<100}".format("",
                                                    "Task cancellation started", ""))

    for task_subset in task_list:
        # list_id = [task["id_task"] for task in task_subset]
        command = "earthengine task cancel {}".format(task_subset)
        command = command.replace(",", "").replace("[", "").replace("]", "").replace("'", "")
        check_output(command, shell=True)

        if verbose:
            counter += len(task_subset)
            print("Tasks cancelled: {:4d}/{} = {:05.2f}%".format(counter, total,
                                                        counter / total * 100))

    if verbose:
        print("{:-<100}\n|{:^98}|\n{:-<100}".format("",
                                                    "Task cancellation finished !", ""))




if __name__ == "__main__":
    # cancelAllTask()
    pass
